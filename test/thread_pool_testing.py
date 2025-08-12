import numpy as np
from concurrent.futures import ThreadPoolExecutor
import subprocess
import os, fire, time
from pathlib import Path
from pyinstrument import Profiler
import csv


class SimulatedCamera:
    def __init__(self, height, width, n_images):
        self.height = height
        self.width = width
        self.n_images = n_images
        self.images = [
            np.random.randint(0, 256, (self.height, self.width), dtype=np.uint8) for _ in range(self.n_images)
        ]
        self.index = 0

    def get_next_image(self):
        if self.index >= self.n_images:
            self.index = 0  # Loop back to start
        img = self.images[self.index]
        self.index += 1
        return img


def create_ffmpeg_process(i, width, height, fps, terminal_output=False):
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "rawvideo",
        "-vcodec",
        "rawvideo",
        "-pix_fmt",
        "gray",
        "-s",
        f"{width}x{height}",
        "-r",
        str(fps),
        "-i",
        "-",
        "-c:v",
        "hevc_nvenc",  # h265 encoding
        f"test/data/output_camera_{i}.mp4",
    ]
    if terminal_output:
        return subprocess.Popen(cmd, stdin=subprocess.PIPE)
    else:
        return subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def get_video_frame_count(video_path):
    """Check the number of frames in a video
    video_path: path to the mp4 file"""
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-count_frames",
        "-show_entries",
        "stream=nb_read_frames",
        "-of",
        "default=nokey=1:noprint_wrappers=1",
        video_path,
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        return int(result.stdout.strip())
    except ValueError:
        return None


def main(
    n_images_generated=5,
    height=1000,
    width=1000,
    fps=30,
    n_camera=1,
    submit_number=200,
    submit_interval=0.01,
    buffer_size=200,
    check_frame_count=True,
    clear_mp4=True,
    terminal_output=False,
):
    """
    Args:
        n_images_generated (int): the number of images of random noise that are generated
        height (int): Vertical resolution of frame
        width (int): Horizontal resolution of frame
        submit_number (int): The number of times the submit function is called per camera
        submit_interval (int): The time between submts of jobs into the threadpool
        clear_mp4 (bool): Remove the mp4s generated if True
    """
    os.makedirs("test/data/", exist_ok=True)

    profiler = Profiler()
    profiler.start()

    print("Starting Threads...")
    executor = ThreadPoolExecutor(max_workers=32)

    print("Creating Cameras...")
    cameras = [SimulatedCamera(height, width, n_images_generated) for _ in range(n_camera)]

    print("Opening FFMPEG Processes...")
    ffmpeg_processes = [create_ffmpeg_process(i, width, height, fps, terminal_output) for i in range(n_camera)]
    time.sleep(2)
    # List to keep track of number of frames recorded per ffmpeg process
    frames_recorded = [0 for _ in range(n_camera)]

    def stream_camera(cam, proc, n_frames):
        for _ in range(n_frames):
            img = cam.get_next_image()
            proc.stdin.write(img.tobytes())

    # Submit data via executor
    print("Submitting FFMPEG jobs...")
    futures = []
    for i in range(submit_number):
        for cam, proc in zip(cameras, ffmpeg_processes):
            future = executor.submit(stream_camera, cam, proc, buffer_size)
            futures.append(future)
            frames_recorded[cameras.index(cam)] += buffer_size
            print("Futures Length:", len(futures))
            futures = [f for f in futures if not f.done()]
        time.sleep(submit_interval)

        # Remove completed futures
    # Overflowing the number of jobs being submitted to the threadpool
    # Monitering the number of jobs currently in the threadpool
    # Ensureing that the threadpool is empty before closing the application
    print("Monitor Futures Length...")
    while len(futures) != 0:
        futures = [f for f in futures if not f.done()]
        print(len(futures))
        time.sleep(submit_interval)
    # Close FFMPEG process
    for proc in ffmpeg_processes:
        proc.stdin.close()
        proc.wait()

    profiler.stop()
    profiler_output_path = "test/data/profiler_report.html"
    profiler.write_html(profiler_output_path)
    print(f"Profiler HTML report saved to {profiler_output_path}")

    print("Finished Encoding.")
    if check_frame_count:
        print("Checking Frame Count...")
        with open("test/data/frame_count_log.csv", "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Camera", "Expected Frames", "Actual Frames", "Match"])
            for i in range(n_camera):
                video_path = f"test/data/output_camera_{i}.mp4"
                expected_frames = frames_recorded[i]
                actual_frames = get_video_frame_count(video_path)
                match = actual_frames == expected_frames
                writer.writerow([i, expected_frames, actual_frames, match])
                print(
                    f"Camera {i}: Expected frames = {expected_frames}, Actual frames = {actual_frames}, Match = {match}"
                )
                if not match:
                    print(f"Warning: Frame count mismatch for camera {i}!")
    else:
        with open("test/data/frame_count_log.csv", "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Camera", "Expected Frames"])
            for i in range(n_camera):
                writer.writerow([i, frames_recorded[i]])
                print(f"Camera {i}: Expected frames = {frames_recorded[i]}")

    if clear_mp4:
        print("Removing MP4 Files from data folder")
        data_dir = Path("test/data/")
        for file in data_dir.glob("*.mp4"):
            file.unlink()

    print("Done")


if __name__ == "__main__":
    fire.Fire(main)
    """How many frames should there be in the file?
    
    The number worker is used and the length of the list does grow and shrink in the way expected. 
    If we do not wait to for the length of the futures to reach 0, then the number of frame recorded will be less than the number of frames that should be recorded
    """
