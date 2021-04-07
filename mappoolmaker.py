from friend_import import *

if TYPE_CHECKING:
    from match import Match_Scrim
    from pydrive import drive

class MappoolMaker:
    def __init__(self, match: 'Match_Scrim', message, name):
        self.match = match
        self.bot = match.bot
        self.loop = self.bot.loop
        self.maps: Dict[str, Tuple[int, int]] = dict()  # MODE: (MAPSET ID, MAPDIFF ID)
        self.osufile_path: Dict[str, str] = dict()
        self.beatmap_objects: Dict[str, osuapi.osu.Beatmap] = dict()
        self.queue = asyncio.Queue()
        self.session: Optional[aiohttp.ClientSession] = self.bot.session
        self.message: Optional[discord.Message] = message
        self.drive_file: Optional[pydrive.drive.GoogleDriveFile] = None

        self.match_made_time = name
        self.pool_name = f"Match_{name}"
        self.save_folder_path = os.path.join('songs', self.pool_name)

    def add_map(self, mode: str, mapid: int, diffid: int):
        self.maps[mode] = (mapid, diffid)

    def remove_map(self, mode: str):
        del self.maps[mode]

    async def downloadBeatmap(self, number: int):
        async with self.session.get(CHIMU + str(number), params=chimu_params) as res_chimu:
            if res_chimu.status == 200:
                async with aiofiles.open(downloadpath % number, 'wb') as f_:
                    await f_.write(await res_chimu.read())
                print(f'{number}번 비트맵셋 다운로드 완료 (chimu.moe)')
            else:
                print(f'{number}번 비트맵셋 다운로드 실패 (chimu.moe) ({res_chimu.status})')
                async with self.session.get(BEATCONNECT + str(number)) as res_beat:
                    if res_beat.status == 200:
                        async with aiofiles.open(downloadpath % number, 'wb') as f_:
                            await f_.write(await res_beat.read())
                        print(f'{number}번 비트맵셋 다운로드 완료 (beatconnect.io)')
                    else:
                        print(f'{number}번 비트맵셋 다운로드 실패 (beatconnect.io) ({res_beat.status})')
                        downloadurl = OSU_BEATMAP_BASEURL + str(number)
                        async with self.session.get(downloadurl + '/download', headers={"referer": downloadurl}) as res:
                            if res.status < 400:
                                async with aiofiles.open(downloadpath % number, 'wb') as f_:
                                    await f_.write(await res.read())
                                print(f'{number}번 비트맵셋 다운로드 완료 (osu.ppy.sh)')
                            else:
                                print(f'{number}번 비트맵셋 다운로드 실패 (osu.ppy.sh) ({res.status})')
                                await self.queue.put((number, False))
                                return
        await self.queue.put((number, True))

    async def show_result(self):
        desc = ''
        has_exception = dd(int)
        success = 0
        await self.message.edit(embed=discord.Embed(
            title="Mappool Downloading",
            color=discord.Colour.orange()
        ))
        try:
            while True:
                v = await self.queue.get()
                if v is None:
                    await self.message.edit(embed=discord.Embed(
                        title="Mappool Download Finished",
                        description=desc,
                        color=discord.Colour.orange()
                    ))
                    break
                if v[1]:
                    success += 1
                    desc += f"Success to download mapId {v[0]} ({success}/{len(self.maps)})\n"
                else:
                    has_exception[v[0]] += 1
                    if has_exception[v[0]] == 3:
                        desc += f"Failed to download mapId{v[0]}\n"
                await self.message.edit(embed=discord.Embed(
                    title="Mappool Downloading",
                    description=desc,
                    color=discord.Colour.orange()
                ))
            return has_exception
        except BaseException as ex_:
            print(get_traceback_str(ex_))
            raise ex_

    async def execute_osz(self) -> Tuple[bool, str]:
        if self.session.closed:
            return False, 'Session is closed'
        t = self.loop.create_task(self.show_result())
        async with asyncpool.AsyncPool(self.loop, num_workers=4, name="DownloaderPool",
                                       logger=logging.getLogger("DownloaderPool"),
                                       worker_co=self.downloadBeatmap, max_task_time=300,
                                       log_every_n=10) as pool:
            for x in self.maps:
                mapid = self.maps[x][0]
                await pool.push(mapid)

        await self.queue.put(None)
        await t

        if 3 in set(t.result().values()):
            return False, 'Map download failed'

        try:
            os.mkdir(self.save_folder_path)
        except FileExistsError:
            pass

        await self.message.edit(embed=discord.Embed(
            title="Extracting `.osz` file and modifying `.osu` files...",
            color=discord.Colour.green()
        ))

        for x in self.maps:
            beatmap_info: osuapi.osu.Beatmap = (await self.bot.osuapi.get_beatmaps(beatmap_id=self.maps[x][1]))[0]
            self.beatmap_objects[x] = beatmap_info

            zipfile_path = downloadpath % beatmap_info.beatmapset_id
            zf = zipfile.ZipFile(zipfile_path)
            target_name = f"{beatmap_info.artist} - {beatmap_info.title} " \
                          f"({beatmap_info.creator}) [{beatmap_info.version}].osu"
            rename_file_name = f"V.A. - {self.pool_name} ({beatmap_info.creator}) " \
                               f"[[{x}] {beatmap_info.artist} - {beatmap_info.title} [{beatmap_info.version}]].osu"
            rename_file_name = prohibitted.sub('', rename_file_name)
            try:
                target_name_search = prohibitted.sub('', target_name.lower())
                zipfile_list = zf.namelist()
                extracted_path = None
                osufile_name = None
                for zfn in zipfile_list:
                    if zfn.lower() == target_name_search:
                        osufile_name = zfn
                        extracted_path = zf.extract(zfn, self.save_folder_path)
                        break
                assert extracted_path is not None
            except AssertionError:
                print(f"파일이 없음 : {target_name}")
                continue

            texts = ''
            async with aiofiles.open(extracted_path, 'r', encoding='utf-8') as osufile:
                texts = await osufile.readlines()
                for i in range(len(texts)):
                    text = texts[i].rstrip()
                    if m := re.match(r'AudioFilename:\s?(.*)', text):
                        audio_path = m.group(1)
                        audio_extracted = zf.extract(audio_path, self.save_folder_path)
                        after_filename = f"{x}.mp3"
                        os.rename(audio_extracted, audio_extracted.replace(audio_path, after_filename))
                        texts[i] = texts[i].replace(audio_path, after_filename)
                    elif m := re.match(r'\d+,\d+,\"(.*?)\".*', text):
                        background_path = m.group(1)
                        extension = background_path.split('.')[-1]
                        bg_extracted = zf.extract(background_path, self.save_folder_path)
                        after_filename = f"{x}.{extension}"
                        os.rename(bg_extracted, bg_extracted.replace(background_path, after_filename))
                        texts[i] = texts[i].replace(background_path, after_filename)
                    elif m := re.match(r'Title(Unicode)?[:](.*)', text):
                        orig_title = m.group(2)
                        texts[i] = texts[i].replace(orig_title, f'Mappool for {self.pool_name}')
                    elif m := re.match(r'Artist(Unicode)?[:](.*)', text):
                        orig_artist = m.group(2)
                        texts[i] = texts[i].replace(orig_artist, f'V.A.')
                    elif m := re.match(r'Version[:](.*)', text):
                        orig_diffname = m.group(1)
                        texts[i] = texts[i].replace(
                            orig_diffname,
                            f"[{x}] {beatmap_info.artist} - {beatmap_info.title} [{beatmap_info.version}]"
                        )

            async with aiofiles.open(extracted_path, 'w', encoding='utf-8') as osufile:
                await osufile.writelines(texts)

            os.rename(extracted_path, extracted_path.replace(osufile_name, rename_file_name))
            self.osufile_path[x] = rename_file_name
            zf.close()
            os.remove(zipfile_path)

        await self.message.edit(embed=discord.Embed(
            title="Compressing Mappool to `.osz`...",
            color=discord.Colour.orange()
        ))

        result_zipfile = f"{self.pool_name}.osz"
        with zipfile.ZipFile(result_zipfile, 'w') as zf:
            for fn in os.listdir(self.save_folder_path):
                zf.write(os.path.join(self.save_folder_path, fn), fn)

        self.drive_file = drive.CreateFile({'title': result_zipfile, 'parents': [{'id': drive_folder['id']}]})
        self.drive_file.SetContentFile(result_zipfile)
        await self.message.edit(embed=discord.Embed(
            title="Uploading Mappool file to Google Drive...",
            description="It takes quite a while. (About 3~5 min.)",
            color=discord.Colour.greyple()
        ))
        try:
            await self.loop.run_in_executor(None, self.drive_file.Upload)
        finally:
            self.drive_file.content.close()
        if self.drive_file.uploaded:
            await self.message.edit(embed=discord.Embed(
                title="Upload Complete!",
                color=discord.Colour.green()
            ))
            self.drive_file.InsertPermission({
                'type': 'anyone',
                'role': 'reader',
                'withLink': True
            })
            os.remove(result_zipfile)
            return True, self.drive_file['alternateLink']
        else:
            await self.message.edit(embed=discord.Embed(
                title="업로드 실패!",
                color=discord.Colour.dark_red()
            ))
            return False, 'Failed'

    async def execute_osz_from_fixca(self, uuid: str):
        if self.session is None:
            return False, 'Session is closed'
        headers = {
            "key": fixca_key,  # INPUT KEY HERE
            "uuid": uuid,
            "matchid": self.match_made_time
        }
        desc = ['Searching Mappool...']
        e = discord.Embed(
            title="Creating Mappool...",
            color=discord.Colour(0xf5e1bf)
        )
        e.description = '\n'.join(desc)
        e.set_footer(text="라카#4749 provided his mappool download server and assisted to making mappool. "
                          "Thanks to supporting!")
        await self.message.edit(embed=e)

        target_beatmap_info = list(filter(lambda po: po['uuid'] == uuid, maidbot_pools))
        if len(target_beatmap_info) == 0:
            return False, 'Not pool found'
        target_beatmap_info = target_beatmap_info[0]
        for mn in target_beatmap_info['maps']:
            self.beatmap_objects[mn['sheetId']] = (await self.bot.osuapi.get_beatmaps(beatmap_id=mn['mapId']))[0]

        desc[-1] += ' done'
        desc.append('Getting download link of mappool...')
        e.description = '\n'.join(desc)
        await self.message.edit(embed=e)

        async with self.session.post("http://ranked-osudroid.kro.kr/createPack", data=headers) as resp:
            if resp.status != 200:
                return False, f'Get info failed : {resp.status}'
            res_data = await resp.json(encoding='utf-8')
            if res_data['status'] == 'failed':
                return False, 'Get info failed : FIXCUCKED'
            download_link = res_data['downlink']
            auto_scores = res_data['autoscore']

        desc[-1] += ' done'
        desc.append('Downloading mappool for setting...')
        e.description = '\n'.join(desc)
        await self.message.edit(embed=e)

        for mm in auto_scores:
            self.match.map_autoscores[mm] = auto_scores[mm]["score"]

        async with self.session.get(download_link) as resp:
            if resp.status != 200:
                return False, f'Download failed : {resp.status}'
            osz_file = self.save_folder_path + '.osz'
            async with aiofiles.open(osz_file, 'wb') as df:
                await df.write(await resp.content.read())
            zf = zipfile.ZipFile(osz_file)
            zf.extractall(self.save_folder_path)
            for fn in os.listdir(self.save_folder_path):
                if fn.endswith(".osu"):
                    m = parse_fixca.match(fn)
                    if m is None:
                        return False, f'Matching failed : {fn}'
                    mapnum = m.group(1)
                    self.osufile_path[mapnum] = fn
            zf.close()
            os.remove(osz_file)

        desc[-1] += ' done'
        e.description = '\n'.join(desc)
        await self.message.edit(embed=e)

        return True, download_link
