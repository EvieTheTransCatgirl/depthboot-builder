from functions import *


def config(de_name: str, distro_version: str, verbose: bool, kernel_version: str) -> None:
    set_verbose(verbose)
    print_status("Configuring Arch")

    # Uncomment worldwide arch mirror
    with open("/mnt/depthboot/etc/pacman.d/mirrorlist", "r") as read:
        mirrors = read.readlines()
    # Uncomment first worldwide mirror
    mirrors[6] = mirrors[6][1:]
    with open("/mnt/depthboot/etc/pacman.d/mirrorlist", "w") as write:
        write.writelines(mirrors)

    # temporarily comment out CheckSpace, coz Pacman fails to check available storage space when run from a chroot
    with open("/mnt/depthboot/etc/pacman.conf", "r") as conf:
        temp_pacman = conf.readlines()
    temp_pacman[34] = f"#{temp_pacman[34]}"
    with open("/mnt/depthboot/etc/pacman.conf", "w") as conf:
        conf.writelines(temp_pacman)

    print_status("Preparing pacman")
    chroot("pacman-key --init")
    chroot("pacman-key --populate archlinux")
    # Add eupnea repo to pacman.conf
    urlretrieve("https://eupnea-project.github.io/arch-repo/public_key.gpg", filename="/mnt/depthboot/tmp/eupnea.key")
    # arch-chroot clears /tmp, so we hae to use normal chroot
    bash("chroot /mnt/depthboot bash -c 'pacman-key --add /tmp/eupnea.key'")
    chroot("pacman-key --lsign-key 94EB01F3608D3940CE0F2A6D69E3E84DF85C8A12")
    # add repo to pacman.conf
    with open("/mnt/depthboot/etc/pacman.conf", "a") as file:
        file.write("[eupnea]\nServer = https://eupnea-project.github.io/arch-repo/repodata/$arch\n")
    chroot("pacman -Syyu --noconfirm")  # update the whole system

    print_status("Installing packages")
    # Install basic utils
    chroot(
        "pacman -S --noconfirm --needed base base-devel nano networkmanager xkeyboard-config linux-firmware sudo bluez "
        "bluez-utils python3 cgpt-vboot-utils zram-generator")
    # install eupnea packages after installing python3
    chroot("pacman -S --noconfirm eupnea-utils eupnea-system")
    # Install kernel
    chroot(f"pacman -S --noconfirm eupnea-{kernel_version}-kernel")

    print_status("Downloading and installing de, might take a while")
    match de_name:
        case "gnome":
            print_status("Installing GNOME")
            chroot("pacman -S --noconfirm gnome gnome-extra")
            chroot("systemctl enable gdm.service")
        case "kde":
            print_status("Installing KDE")
            chroot("pacman -S --noconfirm plasma-meta plasma-wayland-session kde-system-meta kde-utilities-meta "
                   "packagekit-qt5 firefox")
            chroot("systemctl enable sddm.service")
            # Set default kde sddm theme
            mkdir("/mnt/depthboot/etc/sddm.conf.d")
            with open("/mnt/depthboot/etc/sddm.conf.d/breeze-theme.conf", "a") as conf:
                conf.write("[Theme]\nCurrent=breeze")
        case "xfce":
            print_status("Installing Xfce")
            # no wayland support in xfce
            # xfce doesn't have proper audio settings and uses pavucontrol instead
            # xfce does not have any audio servers as dependencies -> manually install pipewire
            chroot("pacman -S --noconfirm xfce4 xfce4-goodies xorg xorg-server lightdm lightdm-gtk-greeter network-"
                   "manager-applet nm-connection-editor xfce4-pulseaudio-plugin pavucontrol pipewire gnome-software "
                   "firefox wireplumber")
            chroot("systemctl enable lightdm.service")
        case "lxqt":
            print_status("Installing LXQt")
            chroot("pacman -S --noconfirm lxqt breeze-icons xorg xorg-server sddm firefox networkmanager-qt "
                   "network-manager-applet nm-connection-editor discover packagekit-qt5")
            chroot("systemctl enable sddm.service")
        case "deepin":
            print_status("Installing deepin")
            chroot("pacman -S --noconfirm deepin deepin-kwin deepin-extra xorg xorg-server lightdm kde-applications "
                   "firefox discover packagekit-qt5")
            # enable deepin specific login style
            with open("/mnt/depthboot/etc/lightdm/lightdm.conf", "a") as conf:
                conf.write("greeter-session=lightdm-deepin-greeter")
            chroot("systemctl enable lightdm.service")
        case "budgie":
            print_status("Installing Budgie")
            chroot("pacman -S --noconfirm lightdm lightdm-gtk-greeter budgie-desktop budgie-desktop-view "
                   "budgie-screensaver budgie-control-center xorg xorg-server network-manager-applet gnome-terminal"
                   " firefox gnome-software nemo")
            chroot("systemctl enable lightdm.service")
            # remove broken gnome xsessions
            chroot("rm /usr/share/xsessions/gnome.desktop")
            chroot("rm /usr/share/xsessions/gnome-xorg.desktop")
        case "cinnamon":
            print_status("Installing Cinnamon")
            chroot("pacman -S --noconfirm cinnamon cinnamon-translations lightdm lightdm-gtk-greeter xed xreader "
                   "gnome-terminal system-config-printer gnome-keyring blueberry")
            chroot("systemctl enable lightdm.service")
            chroot("systemctl enable NetworkManager.service")
        case "cli":
            print_status("Skipping desktop environment install")
        case _:
            print_error(f"Invalid desktop environment: {de_name}. Please create an issue")
            exit(1)

    if de_name != "cli":
        print_status("Installing auto-rotate service, keyd")
        chroot("pacman -S --noconfirm iio-sensor-proxy keyd")

    print_status("Desktop environment setup complete")

    # enable networkmanager systemd service
    chroot("systemctl enable NetworkManager.service")
    # Enable bluetooth systemd service
    chroot("systemctl enable bluetooth")
    # Add zram config
    cpfile("configs/zram/zram-generator.conf", "/mnt/depthboot/etc/systemd/zram-generator.conf")

    # Configure sudo
    # for some reason, the sudoers file sometimes gets reset to default
    # -> create file in /etc/sudoers.d instead to preserve changes
    with open("/mnt/depthboot/etc/sudoers.d/wheel_conf", "w") as conf:
        conf.write("%wheel ALL=(ALL:ALL) ALL")  # enable wheel group to use sudo

    print_status("Restoring pacman config")
    with open("/mnt/depthboot/etc/pacman.conf", "r") as conf:
        temp_pacman = conf.readlines()
    # comment out CheckSpace
    temp_pacman[34] = temp_pacman[34][1:]
    with open("/mnt/depthboot/etc/pacman.conf", "w") as conf:
        conf.writelines(temp_pacman)

    # Kill the gpg-agent processes, as they prevent the image from being unmounted later
    # Find the pids of the correct gpg-agent processes
    gpg_pids = []
    for line in bash("ps aux").split("\n"):
        if "gpg-agent --homedir /etc/pacman.d/gnupg --use-standard-socket --daemon" in line:
            temp_string = line[line.find(" "):].strip()
            gpg_pids.append(temp_string[:temp_string.find(" ")])

    for pid in gpg_pids:
        print(f"Killing gpg-agent proces with pid: {pid}")
        bash(f"kill {pid}")

    print_status("Arch setup complete")
