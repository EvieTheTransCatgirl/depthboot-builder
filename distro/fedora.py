from functions import *


def config(de_name: str, distro_version: str, verbose: bool, kernel_version: str) -> None:
    set_verbose(verbose)
    print_status("Configuring Fedora")

    # Tweak dnf config to enable multithreaded downloads
    with open("/mnt/depthboot/etc/dnf/dnf.conf", "r") as f:
        og_dnf_conf = f.read()
    new_dnf_conf = og_dnf_conf.replace("installonly_limit=3", "installonly_limit=0")
    new_dnf_conf += "\nfastestmirror=True\nmax_parallel_downloads=10\n"
    with open("/mnt/depthboot/etc/dnf/dnf.conf", "w") as f:
        f.write(new_dnf_conf)

    print("Installing dependencies")
    chroot(f"dnf install -y --releasever={distro_version} fedora-release")  # update repos list
    # Add eupnea repo
    chroot("dnf config-manager --add-repo https://eupnea-project.github.io/rpm-repo/eupnea.repo")
    chroot("dnf update --refresh -y")  # update repos
    # Install eupnea packages
    chroot("dnf install -y eupnea-system eupnea-utils")
    # Install kernel
    chroot(f"dnf install -y eupnea-{kernel_version}-kernel")
    # Install core packages
    chroot("dnf group install -y 'Core'")
    # Install firmware packages
    chroot("dnf group install -y 'Hardware Support'")
    chroot("dnf group install -y 'Common NetworkManager Submodules'")
    chroot("dnf install -y linux-firmware")

    print_status("Downloading and installing DE, might take a while")
    match de_name:
        case "gnome":
            print_status("Installing GNOME")
            chroot("dnf group install -y 'Fedora Workstation'")  # Fedora has gnome by default in a workstation install
            chroot("dnf install -y firefox")
        case "kde":
            print_status("Installing KDE")
            chroot("dnf group install -y 'KDE Plasma Workspaces'")
            chroot("dnf install -y firefox")
        case "xfce":
            print_status("Installing Xfce")
            chroot("dnf group install -y 'Xfce Desktop'")
            chroot("dnf install -y firefox gnome-software xfce4-pulseaudio-plugin")
        case "lxqt":
            print_status("Installing LXQt")
            chroot("dnf group install -y 'LXQt Desktop'")
            chroot("dnf install -y plasma-discover")
        case "deepin":
            print_status("Installing deepin")
            chroot("dnf group install -y 'Deepin Desktop'")
            chroot("dnf install -y plasma-discover")
        case "budgie":
            print_status("Installing Budgie")
            chroot("dnf install -y budgie-desktop lightdm lightdm-gtk xorg-x11-server-Xorg gnome-terminal firefox "
                   "gnome-software nemo")
        case "cinnamon":
            print_status("Installing Cinnamon")
            chroot("dnf group install -y 'Cinnamon Desktop'")
        case "cli":
            print_status("Skipping desktop environment install")
            # install network tui
            chroot("dnf install -y NetworkManager-tui")
        case _:
            print_error("Invalid desktop environment! Please create an issue")
            exit(1)

    if de_name != "cli":
        # Set system to boot to gui
        chroot("systemctl set-default graphical.target")
        # install keyd
        chroot("dnf install -y keyd")
    print_status("Desktop environment setup complete")

    # Add zram config
    cpfile("configs/zram/zram-generator.conf", "/mnt/depthboot/etc/systemd/zram-generator.conf")

    # Restore dnf config
    with open("/mnt/depthboot/etc/dnf/dnf.conf", "w") as f:
        f.write(og_dnf_conf)

    print_status("Fedora setup complete")
