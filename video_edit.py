from moviepy import VideoFileClip


def convert_video_to_audio(video_path, audio_path):
    """
    Convert video file to audio file.
    """
    video = VideoFileClip(video_path)
    audio = video.audio
    audio.write_audiofile(audio_path)

if __name__ == "__main__":
    video_path = "example_video.mp4"  # Replace with your video file path
    audio_path = "output_audio.wav"  # Desired output audio file path
    convert_video_to_audio(video_path, audio_path)
    print(f"Audio extracted to: {audio_path}")