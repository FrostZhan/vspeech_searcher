from video_searcher import VideoSpeechContentSearcher


vs = VideoSpeechContentSearcher()
vs.delete_database("test_db")
vs.use_database("test_db")

vs.add_videos(["牛肉丸1.mp4", "牛肉丸2.mp4"])
vs.user_query()



