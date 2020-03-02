import imageio
import glob
import moviepy.editor as mp


images = []

filenames = glob.glob('./meanByTempBaseline/**.png')
filenames.sort()
for filename in filenames:
    images.append(imageio.imread(filename))

dest = 'avgCorByBaseline.gif'
imageio.mimsave(dest, images, duration=0.32)

clip = mp.VideoFileClip(dest)
# clip.write_videofile(dest.replace('.gif', '.mp4'))