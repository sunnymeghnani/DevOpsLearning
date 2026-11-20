# Verify VM runner: QEMU/KVM in a container, so a throwaway Ubuntu 24.04 VM can run the handbook's
# commands and lab rooms without installing anything on the host (labs/vm/README.md).
#
#   python3 labs/vm/vmctl.py check        builds this image (devops-handbook-vm:local) if needed
#
# vmctl.py starts it ONLY as: docker run --device /dev/kvm --cap-drop ALL --security-opt no-new-privileges
# --read-only, no published ports, the named volume devops-handbook-vm on /vm. QEMU's user-mode network
# forwards the guest's SSH to 127.0.0.1 INSIDE this container; vmctl reaches it with `docker exec ... ssh`.
# The first step is a no-op `RUN : devops-handbook-vm`: its build-cache record is unique to this Dockerfile,
# so docker/janitor/janitor.py can tell this project's cache from other projects'.
FROM ubuntu:24.04 AS devops-handbook-vm
RUN : devops-handbook-vm
LABEL devops-handbook.project="vm" org.opencontainers.image.title="devops-handbook-vm"
ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8
# qemu-system-x86 + qemu-utils: the VM and qcow2 overlays; genisoimage: the cloud-init NoCloud seed;
# gpgv + ubuntu-keyring: verify SHA256SUMS.gpg against ubuntu-cloudimage-keyring.gpg before the image is used
RUN apt-get update \
 && apt-get install -y --no-install-recommends qemu-system-x86 qemu-utils genisoimage openssh-client \
      gpgv ubuntu-keyring ca-certificates curl python3 \
 && apt-get clean && rm -rf /var/lib/apt/lists/* \
 && test -s /usr/share/keyrings/ubuntu-cloudimage-keyring.gpg
WORKDIR /vm
CMD ["sleep", "infinity"]
