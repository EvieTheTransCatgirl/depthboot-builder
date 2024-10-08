from functions import *


def config(de_name: str, distro_version: str, verbose: bool, kernel_version: str) -> None:
    set_verbose(verbose)
    print_status("Configuring Pop!_OS")

    print_status("Removing casper debs")
    # List of packages to remove was taken from /cdrom/casper/filesystem.manifest-remove from the iso
    chroot("apt-get purge -y btrfs-progs casper cifs-utils distinst distinst-v2 dmraid expect f2fs-tools fatresize "
           "gettext gparted gparted-common grub-common grub2-common kpartx kpartx-boot libdistinst libdmraid1.0.0.rc16"
           " libinih1 libnss-mymachines localechooser-data os-prober pop-installer pop-installer-casper pop-shop-casper"
           " squashfs-tools systemd-container tcl-expect user-setup xfsprogs kernelstub efibootmgr")

    print_status("Installing eupnea repo package")
    # Install eupnea repo package
    urlretrieve(f"https://github.com/eupnea-project/deb-repo/releases/latest/download/eupnea-jammy-keyring.deb",
                filename="/mnt/depthboot/tmp/keyring.deb")
    chroot("apt-get install -y /tmp/keyring.deb")
    # remove keyring package
    rmfile("/mnt/depthboot/tmp/keyring.deb")

    # update apt
    print_status("Updating and upgrading all packages")
    chroot("apt-get update -y")
    chroot("apt-get upgrade -y")
    print_status("Installing eupnea packages")
    # Install eupnea packages
    chroot("apt-get install -y eupnea-utils eupnea-system keyd")

    # Install kernel
    chroot(f"apt-get install -y eupnea-{kernel_version}-kernel")

    # Replace input-synaptics with newer input-libinput, for better touchpad support
    print_status("Upgrading touchpad drivers")
    chroot("apt-get remove -y xserver-xorg-input-synaptics")
    chroot("apt-get install -y xserver-xorg-input-libinput")

    # Enable wayland
    print_status("Enabling Wayland")
    with open("/mnt/depthboot/etc/gdm3/custom.conf", "r") as file:
        gdm_config = file.read()
    with open("/mnt/depthboot/etc/gdm3/custom.conf", "w") as file:
        file.write(gdm_config.replace("WaylandEnable=false", "#WaylandEnable=false"))
    # TODO: Set wayland as default

    print_status("Pop!_OS setup complete")
