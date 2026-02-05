from pyncm import apis
import argparse
import pyperclip


def get_playlist_data(playlist_id):
    """获取播放列表的所有歌曲信息"""
    apis.login.LoginViaAnonymousAccount()
    offset = 0
    limit = 1000
    result = []

    while True:
        data = apis.playlist.GetPlaylistAllTracks(
            playlist_id, offset=offset, limit=limit
        )["songs"]
        if not data:
            break
        for track in data:
            name = track["name"]
            album_name = track["al"]["name"]
            artist = "/".join(artist["name"] for artist in track.get("ar", []))
            result.append({"name": name, "artist": artist, "album": album_name})
        offset += limit

    return result


def copy_to_clipboard(song_info):
    """将格式化的歌曲信息复制到剪贴板"""
    formatted_info = f"歌名: {song_info['name']}; 艺术家: {song_info['artist']}; 专辑: {song_info['album']}"
    pyperclip.copy(formatted_info)
    print(f"已复制到剪贴板: {formatted_info}")


def copy_all_to_clipboard(playlist_data):
    """将所有歌曲信息格式化并复制到剪贴板"""
    formatted_info = "\n".join(
        [
            f"歌名: {song['name']}; 艺术家: {song['artist']}; 专辑: {song['album']}"
            for song in playlist_data
        ]
    )
    pyperclip.copy(formatted_info)
    print("已复制所有歌曲信息到剪贴板。")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="获取网易云音乐播放列表的歌曲信息")
    parser.add_argument("playlist_id", help="播放列表 ID")
    args = parser.parse_args()

    playlist_data = get_playlist_data(args.playlist_id)
    for i, song in enumerate(playlist_data, start=1):
        print(
            f"{i}. 歌名: {song['name']}; 艺术家: {song['artist']}; 专辑: {song['album']}"
        )

    copy_all_to_clipboard(playlist_data)
