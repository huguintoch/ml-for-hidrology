import os

import matplotlib.pyplot as plt
import numpy as np
import paramiko
import skimage

STPF_URL = ''
STPF_USER = ''
STPF_PASS = ''
ROOT_PATH = ''


def init_ssh():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(STPF_URL, username=STPF_USER, password=STPF_PASS)
    return ssh


def load_checkpoint():
    try:
        checkpoint_dict = np.load(
            'checkpoint_dict.npy', allow_pickle=True).item()
        print('Checkpoint loaded. Keys: ', checkpoint_dict.keys())
    except:
        checkpoint_dict = {}
        print('No checkpoint file found. Creating new checkpoint.')
    return checkpoint_dict


def init_csv():
    if not os.path.exists('data.csv'):
        with open('data.csv', 'w') as f:
            headers = 'Filename,' + \
                ','.join(['bin'+str(i) for i in range(360)]) + '\n'
            f.write(headers)


def format_line(filename, hue_percentages):
    line = filename + ',' + ','.join([str(i) for i in hue_percentages]) + '\n'
    return line


def add_line_to_csv(line):
    with open('data.csv', 'a') as f:
        f.write(line)


def save_checkpoint(checkpoint_dict):
    np.save('checkpoint_dict.npy', checkpoint_dict)


def get_hue_percentages(img):
    hsv = skimage.color.rgb2hsv(img)
    hue = hsv[:, :, 0].flatten()
    hue_percentages = np.histogram(hue, bins=360, range=(0, 1))[0] / len(hue)
    hue_percentages = [round(i, 3) for i in hue_percentages]
    return hue_percentages


def main():
    ssh = init_ssh()
    ftp = ssh.open_sftp()

    ftp.chdir(ROOT_PATH)
    root_subdirs = ftp.listdir()
    checkpoint_dict = load_checkpoint()

    init_csv()

    try:
        root_subdirs_len = len(root_subdirs)
        for subdir_index, subdir in enumerate(root_subdirs):
            if subdir not in checkpoint_dict:
                checkpoint_dict[subdir] = {}

            ftp.chdir(subdir)
            files = ftp.listdir()

            dir_len = len(files)
            for file_index, file in enumerate(files):
                if file not in checkpoint_dict[subdir]:
                    ftp.get(file, 'image_being_processed.jpg')
                    try:
                        image = skimage.io.imread('image_being_processed.jpg')
                    except:
                        print('Error reading image {}. Skipping...'.format(file))
                        continue
                    hue_percentages = get_hue_percentages(image)
                    add_line_to_csv(format_line(file, hue_percentages))
                    checkpoint_dict[subdir][file] = 1
                    save_checkpoint(checkpoint_dict)
                    print('Processed file {}/{} in dir {}/{}.'.format(file_index +
                          1, dir_len, subdir_index+1, root_subdirs_len))
                else:
                    print('Already processed file {}/{} in dir {}/{}.'.format(file_index +
                          1, dir_len, subdir_index+1, root_subdirs_len))
            ftp.chdir('..')
    except:
        print('Error: ', e)
    finally:
        ftp.close()
        ssh.close()


if __name__ == '__main__':
    main()
