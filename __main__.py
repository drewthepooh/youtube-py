from subprocess import Popen, PIPE

if __name__ == '__main__':

    youtube = Popen(['python', 'youtube.py'], stdout=PIPE)
    less = Popen(['less'], stdin=youtube.stdout)

    youtube.wait()
    less.wait()

    print('done')

