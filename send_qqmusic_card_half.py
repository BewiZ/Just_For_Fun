from ncatbot.plugin import BasePlugin, CompatibleEnrollment
from ncatbot.core.message import GroupMessage
from ncatbot.utils.logger import get_log
from ncatbot.core.element import *

import requests, json, time, uuid
import logging

_log = get_log()
bot = CompatibleEnrollment


class QQMusicSender:
    """QQ音乐消息构造器（独立服务类）"""

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36",
            "Referer": "https://y.qq.com/",
        }

    def search_song(self, song_name: str, artist: str = "") -> dict:
        """搜索歌曲信息"""
        url = "https://c.y.qq.com/soso/fcgi-bin/client_search_cp"
        params = {"w": f"{song_name} {artist}".strip(), "format": "json", "p": 1, "n": 1}

        try:
            resp = requests.get(url, headers=self.headers, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            song_list = data.get("data", {}).get("song", {}).get("list", [])
            if not song_list:
                raise ValueError("未找到匹配歌曲")

            song_info = song_list[0]
            return {
                "songname": song_info.get("songname", ""),
                "songmid": song_info.get("songmid", ""),
                "albummid": song_info.get("albummid", ""),
                "interval": song_info.get("interval", 0),
                "singer": "/".join([s["name"] for s in song_info.get("singer", [])]),
            }

        except Exception as e:
            logging.error(f"歌曲搜索失败: {str(e)}")
            return {}

    def get_music_url(self, songmid: str) -> dict:
        guid = str(uuid.uuid4()).replace("-", "").upper()
        play_url = "https://u.y.qq.com/cgi-bin/musicu.fcg"
        payload = {
            "req_0": {
                "module": "vkey.GetVkeyServer",  # 指定调用的服务模块（获取播放密钥的模块）
                "method": "CgiGetVkey",  # 指定调用的方法（生成播放链接的核心方法）
                "param": {  # 具体请求参数：
                    "guid": guid,  # 设备唯一标识符（需随机生成，如用 uuid 库生成，用于反爬虫追踪）
                    "songmid": [songmid],  # 歌曲唯一标识（从搜索接口获取的 songmid，支持批量查询）
                    "songtype": [0],  # 歌曲类型：0-普通歌曲，1-无损音质（需VIP）
                    "uin": "0",  # 用户ID：0-未登录用户，非零值-登录用户的QQ号（需Cookie授权）
                    "platform": "20",  # 平台标识：20-网页端，1-iOS，2-Android
                },
            },
            "comm": {
                "uin": 0,  # 用户ID（与 req_0.param.uin 一致）
                "format": "json",  # 返回数据格式（固定为 json）
                "ct": 24,  # 客户端类型：24-网页端，25-移动端
                "cv": 0,  # 客户端版本号（0 表示不校验版本）
            },
        }
        response = requests.post(play_url, headers=self.headers, data=json.dumps(payload))
        data = response.json()
        print(data)
        if data.get("req_0"):
            return {
                "purl": data["req_0"]["data"]["midurlinfo"][0]["purl"],
                "vkey": data["req_0"]["data"]["midurlinfo"][0]["vkey"],
                "guid": guid,
            }
        return None


class plugin_3(BasePlugin):
    name = "QQ音乐插件"
    version = "1.1.0"

    def __init__(self, time_task_scheduler, event_bus, config=None, **kwargs):
        super().__init__(time_task_scheduler=time_task_scheduler, event_bus=event_bus, config=config, **kwargs)
        self.music_sender = QQMusicSender()

    def _build_music_json(self, song_info: dict) -> dict:
        """构建分享JSON结构"""
        # 获取播放参数
        play_params = self.music_sender.get_music_url(song_info["songmid"])

        # 生成时间戳和随机参数
        ctime = int(time.time())
        token = str(uuid.uuid4()).replace("-", "")[:16]

        return {
            "app": "com.tencent.music.lua",
            "bizsrc": "qqconnect.sdkshare_music",
            "prompt": f"[分享]{song_info['songname']}",
            "ver": "0.0.0.1",
            "view": "music",
            "config": {"ctime": ctime, "forward": 1, "token": token, "type": "normal"},
            "extra": {"app_type": 1, "appid": 100497308, "msg_seq": int(uuid.uuid4().hex[:16], 16), "uin": 0},
            "meta": {
                "music": {
                    "app_type": 1,
                    "appid": 100497308,
                    "ctime": ctime,
                    "desc": "推荐歌曲",
                    "jumpUrl": f"https://y.qq.com/n/ryqq/songDetail/{song_info['songmid']}",
                    "musicUrl": f"http://ws.stream.qqmusic.qq.com/{play_params['purl']}",
                    "preview": f"https://y.gtimg.cn/music/photo_new/T002R150x150M000{song_info['albummid']}_2.jpg",
                    "tag": "音乐",
                    "title": song_info["songname"],
                    "uin": 0,
                    "duration": song_info["interval"],  # 单位：秒
                }
            },
        }

    @bot.group_event()
    async def on_group_event(self, msg: GroupMessage):
        try:
            if msg.raw_message.strip() == "/测试yy":
                # 步骤1: 搜索歌曲
                song_info = self.music_sender.search_song("UNFADING", "MIMI")
                if not song_info:
                    await self.api.post_group_msg(msg.group_id, Text("找不到指定歌曲"))
                    return

                # 步骤2: 构建消息
                music_json = self._build_music_json(song_info)
                message = MessageChain([Json(music_json)])

                # 步骤3: 发送消息
                await self.api.post_group_msg(group_id=msg.group_id, rtf=message)
                _log.info(f"成功发送音乐卡片: {song_info['songname']}")

        except Exception as e:
            _log.error(f"消息处理异常: {str(e)}")
            await self.api.post_group_msg(msg.group_id, Text(f"服务异常: {str(e)}"))

    async def on_load(self):
        _log.info(f"已注入参数: {self.time_task_scheduler}, {self.event_bus}")
        _log.info(f"{self.name} v{self.version} 初始化完成")

    async def on_unload(self):
        _log.info(f"{self.name} 插件已卸载")
