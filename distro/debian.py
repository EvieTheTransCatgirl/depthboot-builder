from functions import *


def config(de_name: str, distro_version: str, verbose: bool, kernel_version: str) -> None:
    set_verbose(verbose)
    print_status("Configuring Debian")

    # Copy over sources.list (the bootstrap one doesn't have all the stock debian repos)
    cpfile("configs/debian-sources.list", "/mnt/depthboot/etc/apt/sources.list")

    print_status("Installing eupnea repo package")
    urlretrieve(f"https://github.com/eupnea-project/deb-repo/releases/latest/download/eupnea-{distro_version}-"
                f"keyring.deb", filename="/mnt/depthboot/tmp/keyring.deb")
    chroot("apt-get install -y /tmp/keyring.deb")
    # remove keyring package
    rmfile("/mnt/depthboot/tmp/keyring.deb")

    # update apt
    chroot("apt-get update -y")
    chroot("apt-get upgrade -y")
    # Install general dependencies + eupnea packages
    print_status("Installing dependencies")
    chroot("apt-get install -y network-manager sudo firmware-linux-free firmware-linux-nonfree "
           "firmware-iwlwifi iw")
    chroot("apt-get update -y")
    chroot("apt-get install -y eupnea-utils eupnea-system")

    # Install kernel
    chroot(f"apt-get install -y eupnea-{kernel_version}-kernel")

    # Install zram
    chroot("apt-get install -y systemd-zram-generator")
    # Add zram config
    cpfile("configs/zram/zram-generator.conf", "/mnt/depthboot/etc/systemd/zram-generator.conf")

    print_status("Downloading and installing de, might take a while")
    # DEBIAN_FRONTEND=noninteractive skips locale setup questions
    # package names taken from https://www.debian.org/doc/manuals/debian-reference/ch07.en.html
    match de_name:
        case "gnome":
            print_status("Installing GNOME")
            chroot("DEBIAN_FRONTEND=noninteractive apt-get install -y task-gnome-desktop")
        case "kde":
            print_status("Installing KDE")
            chroot("DEBIAN_FRONTEND=noninteractive apt-get install -y task-kde-desktop")
        case "xfce":
            print_status("Installing Xfce")
            chroot("DEBIAN_FRONTEND=noninteractive apt-get install -y task-xfce-desktop xfce4-pulseaudio-plugin "
                   "gnome-software epiphany-browser")
        case "lxqt":
            print_status("Installing LXQt")
            chroot("DEBIAN_FRONTEND=noninteractive apt-get install -y task-lxqt-desktop plasma-discover")
        case "deepin":
            print_error("Deepin is not available for Debian")
            exit(1)
        case "budgie":
            print_status("Installing Budgie")
            chroot("DEBIAN_FRONTEND=noninteractive apt-get -y --install-suggests install budgie-desktop lightdm "
                   "lightdm-gtk-greeter epiphany-browser gnome-software")
            chroot("systemctl enable lightdm.service")
        case "cinnamon":
            print_status("Installing Cinnamon")
            chroot("DEBIAN_FRONTEND=noninteractive apt-get install -y task-cinnamon-desktop")
        case "cli":
            print_status("Skipping desktop environment install")
        case _:
            print_error("Invalid desktop environment! Please create an issue")
            exit(1)

    if de_name != "cli":
        # Set system to boot to gui
        chroot("systemctl set-default graphical.target")
        # Replace input-synaptics with newer input-libinput, for better touchpad support
        print_status("Upgrading touchpad drivers")
        chroot("apt-get remove -y xserver-xorg-input-synaptics")
        chroot("apt-get install -y xserver-xorg-input-libinput")
        print_status("Installing keyd")
        chroot("apt-get install -y keyd")

    # GDM3 auto installs gnome-minimal. Remove it if user didn't choose gnome
    if de_name != "gnome":
        # rmfile("/mnt/depthboot/usr/share/xsessions/debian.desktop")
        chroot("apt-get remove -y gnome-shell")
        chroot("apt-get autoremove -y")

    # Fix gdm3, https://askubuntu.com/questions/1239503/ubuntu-20-04-and-20-10-etc-securetty-no-such-file-or-directory
    with contextlib.suppress(FileNotFoundError):
        cpfile("/mnt/depthboot/usr/share/doc/util-linux/examples/securetty", "/mnt/depthboot/etc/securetty")
    print_status("Desktop environment setup complete")

    print_status("Debian setup complete")
