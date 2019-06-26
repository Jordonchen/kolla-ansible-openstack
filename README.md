# kolla-ansible-openstack
use kolla-ansible to build OpenStack Platform

一、	项目环境
工具：VMware workstation
系统：centos7
配置：内存16G以上，CPU 4核以上，3个网卡。
说明：可用服务器直连物理网络进行部署，本项目因考虑实验便利，选择在VMware环境下部署all-in-one模式。本部署可完全支持ipv6环境，本次部署采用ipv4和私有ipv6地址并存的方式。
二、	部署过程：
1、启动虚拟机
配置如下：
•	内存： 16G(建议再高点)
•	处理器：4核（开启嵌套虚拟化） 
•	硬盘：150G（系统盘） + 60GB(创建cinder lvm时使用)
•	网络：2个NAT网络，1个仅主机网络（网络适配器、网络适配器2为NAT，网络适配器3为仅主机模式）
配置网络：
3张网卡规划如下：
ens33: NAT网卡，服务器上网用，static，配置ip，可以上网。
ens34: NAT网卡，OpenStack public网，static，不配置ip。
ens35: 仅主机模式网卡，OpenStack管理网，static，配置ip，无法上网。
网卡具体配置：
编辑ens33
vi /etc/sysconfig/network-scripts/ifcfg-ens33
TYPE=Ethernet
PROXY_METHOD=none
BROWSER_ONLY=no
BOOTPROTO=static 
DEFROUTE=yes
IPV4_FAILURE_FATAL=no
IPV6INIT=yes
IPV6_AUTOCONF=yes
IPV6_DEFROUTE=yes
IPV6_FAILURE_FATAL=no
IPV6_ADDR_GEN_MODE=stable-privacy
NAME=ens33
UUID=f0ce559b-e74a-4c9a-bb69-fc7f46f03244
DEVICE=ens33
ONBOOT=yes 
# 增加如下内容
GATEWAY=192.168.159.2  # NAT模式得网关
IPADDR=192.168.159.130   # NAT模式网关处于同一网段
NETMASK=255.255.255.0
DNS1=114.114.114.114
重启网络：systemctl restart network
重启后，可以ping通百度。

编辑ens34
此网卡不配置ip。
vi /etc/sysconfig/network-scripts/ifcfg-ens34
TYPE=Ethernet
PROXY_METHOD=none
BROWSER_ONLY=no
BOOTPROTO=dhcp
DEFROUTE=yes
IPV4_FAILURE_FATAL=no
IPV6INIT=yes
IPV6_AUTOCONF=yes
IPV6_DEFROUTE=yes
IPV6_FAILURE_FATAL=no
IPV6_ADDR_GEN_MODE=stable-privacy
NAME=ens34
UUID=2523942d-4141-45d8-8d58-debc36e5af07
DEVICE=ens34
ONBOOT=no
编辑ens35
vi /etc/sysconfig/network-scripts/ifcfg-ens35
TYPE=Ethernet
PROXY_METHOD=none
BROWSER_ONLY=no
BOOTPROTO=static 
DEFROUTE=yes
IPV4_FAILURE_FATAL=no
IPV6INIT=yes
IPV6_AUTOCONF=yes
IPV6_DEFROUTE=yes
IPV6_FAILURE_FATAL=no
IPV6_ADDR_GEN_MODE=stable-privacy
NAME=ens35
UUID=7933698a-9938-4809-b6db-2f80983a2214
DEVICE=ens35
ONBOOT=yes 
# 增加如下内容
IPADDR=192.168.226.130   #仅主机模式网段
NETMASK=255.255.255.0
重启网络：systemctl restart network

2、配置cinder存储
虚拟机上的60GB硬盘在本实验中为 sdb
pvcreate /dev/sdb
vgcreate cinder-volumes /dev/sdb

3、配置加速源
yum 加速源(centos7 阿里源)
yum install -y wget
mv /etc/yum.repos.d/CentOS-Base.repo /etc/yum.repos.d/CentOS-Base.repo.backup
wget -O /etc/yum.repos.d/CentOS-Base.repo http://mirrors.aliyun.com/repo/Centos-7.repo
wget -O /etc/yum.repos.d/epel.repo http://mirrors.aliyun.com/repo/epel-7.repo
yum clean all
yum makecache
4、pip 加速源(阿里源)
mkdir ~/.pip
cat > ~/.pip/pip.conf << EOF 
[global]
trusted-host=mirrors.aliyun.com
index-url=https://mirrors.aliyun.com/pypi/simple/
EOF
5、docker 加速源（阿里源）
mkdir /etc/docker
cat > /etc/docker/daemon.json << EOF
{
  "registry-mirrors": ["https://jzngeu7d.mirror.aliyuncs.com"]
}
EOF
6、配置iptables
yum install iptables -y
yum install iptables-services -y
systemctl start iptables.service
systemctl enable iptables.service

iptables -F
iptables -P INPUT ACCEPT
iptables -P OUTPUT ACCEPT
iptables -P FORWARD ACCEPT
service iptables save
systemctl restart iptables.service
至此基础环境准备完成。

7、kolla-ansible 部署
7.1、安装软件环境
yum install -y epel-release 
yum install -y python-pip
pip install -U pip
yum install -y python-devel libffi-devel gcc openssl-devel libselinux-python
yum install -y ansible
pip install -U ansible
编辑ansible配置文件，在defaults中添加3个属性
vim /etc/ansible/ansible.cfg
[defaults]
host_key_checking=False
pipelining=True
forks=100
7.2、安装 kolla-ansible
pip install kolla-ansible==7.0.0
cp -r /usr/share/kolla-ansible/etc_examples/kolla /etc/
cp /usr/share/kolla-ansible/ansible/inventory/* /opt/
7.3、配置主要文件
这里有4个文件，简单介绍：
•	/etc/kolla/globals.yml 决定要装什么组件和openstack基础配置
•	/etc/kolla/passwords.yml 可以定义openstack各组件密码
•	/opt/all-in-one 决定openstack组件安装得物理位置
•	/opt/multinode 决定openstack组件安装得物理位置
7.4、开始配置：
对于passwords.yml：
kolla-genpwd，这命令生成随机码作为密码使用，可以更改keystone_admin=123456，方便自己登陆。
对于globals.yml：
此文件包含两部分内容：openstack基础配置，选择安装的openstack组件。
vim /etc/kolla/globals.yml 
kolla_base_distro: "centos"  # 基础容器镜像版本
kolla_install_type: "source"  # 源码安装方式安装组件
openstack_release: "queens"  # openstack版本，选择你需要的
network_interface: "ens35"  # 管理网使用的网卡
neutron_external_interface: "ens34"  # public网使用得网卡
kolla_internal_vip_address: "192.168.226.131"  # 服务内部地址。
kolla_external_vip_address: "192.168.159.131"  # 服务外部地址。
enable_cinder: "yes"
enable_cinder_backend_lvm: "yes"
cinder_volume_group: "cinder-volumes"
enable_horizon: "yes"
nova_compute_virt_type=qemu

8、开始部署
kolla-ansible -i /opt/all-in-one bootstrap-servers
kolla-ansible -i /opt/all-in-one prechecks
kolla-ansible -i /opt/all-in-one deploy
9、基本使用
安装命令行工具：
pip install python-openstackclient python-glanceclient python-neutronclient
确认部署（会生成管理员密码等）：
kolla-ansible post-deploy
导入环境变量：
source /etc/kolla/admin-openrc.sh
查看服务状态：
openstack service list --long
至此openstack基本环境以及搭建完成。

