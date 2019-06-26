# kolla-ansible-openstack
use kolla-ansible to build OpenStack Platform

## 一、	项目环境 <br>
工具：VMware workstation<br>
系统：centos7<br>
配置：内存16G以上，CPU 4核以上，3个网卡。<br>
说明：可用服务器直连物理网络进行部署，本项目因考虑实验便利，选择在VMware环境下部署all-in-one模式。本部署可完全支持ipv6环境，本次部署采用ipv4和私有ipv6地址并存的方式。<br>
## 二、	部署过程：<br>
### 1、启动虚拟机<br>
配置如下：<br>
•	内存： 16G(建议再高点)<br>
•	处理器：4核（开启嵌套虚拟化） <br>
•	硬盘：150G（系统盘） + 60GB(创建cinder lvm时使用)<br>
•	网络：2个NAT网络，1个仅主机网络（网络适配器、网络适配器2为NAT，网络适配器3为仅主机模式）<br>
配置网络：<br>
3张网卡规划如下：<br>
ens33: NAT网卡，服务器上网用，static，配置ip，可以上网<br>
ens34: NAT网卡，OpenStack public网，static，不配置ip。<br>
ens35: 仅主机模式网卡，OpenStack管理网，static，配置ip，无法上网。<br>
网卡具体配置：<br>
编辑ens33<br>
vi /etc/sysconfig/network-scripts/ifcfg-ens33<br>
TYPE=Ethernet<br>
PROXY_METHOD=none<br>
BROWSER_ONLY=no<br>
BOOTPROTO=static <br>
DEFROUTE=yes<br>
IPV4_FAILURE_FATAL=no<br>
IPV6INIT=yes<br>
IPV6_AUTOCONF=yes<br>
IPV6_DEFROUTE=yes<br>
IPV6_FAILURE_FATAL=no<br>
IPV6_ADDR_GEN_MODE=stable-privacy<br>
NAME=ens33<br>
UUID=f0ce559b-e74a-4c9a-bb69-fc7f46f03244<br>
DEVICE=ens33<br>
ONBOOT=yes <br>
增加如下内容<br>
GATEWAY=192.168.159.2  # NAT模式得网关<br>
IPADDR=192.168.159.130   # NAT模式网关处于同一网段<br>
NETMASK=255.255.255.0<br>
DNS1=114.114.114.114<br>
重启网络：systemctl restart network<br>
重启后，可以ping通百度。<br>

编辑ens34<br>
此网卡不配置ip。<br>
vi /etc/sysconfig/network-scripts/ifcfg-ens34<br>
TYPE=Ethernet<br>
PROXY_METHOD=none<br>
BROWSER_ONLY=no<br>
BOOTPROTO=dhcp<br>
DEFROUTE=yes<br>
IPV4_FAILURE_FATAL=no<br>
IPV6INIT=yes<br>
IPV6_AUTOCONF=yes<br>
IPV6_DEFROUTE=yes<br>
IPV6_FAILURE_FATAL=no<br>
IPV6_ADDR_GEN_MODE=stable-privacy<br>
NAME=ens34<br>
UUID=2523942d-4141-45d8-8d58-debc36e5af07<br>
DEVICE=ens34<br>
ONBOOT=no<br>
编辑ens35<br>
vi /etc/sysconfig/network-scripts/ifcfg-ens35<br>
TYPE=Ethernet<br>
PROXY_METHOD=none<br>
BROWSER_ONLY=no<br>
BOOTPROTO=static <br>
DEFROUTE=yes<br>
IPV4_FAILURE_FATAL=no<br>
IPV6INIT=yes<br>
IPV6_AUTOCONF=yes<br>
IPV6_DEFROUTE=yes<br>
IPV6_FAILURE_FATAL=no<br>
IPV6_ADDR_GEN_MODE=stable-privacy<br>
NAME=ens35<br>
UUID=7933698a-9938-4809-b6db-2f80983a2214<br>
DEVICE=ens35<br>
ONBOOT=yes <br>
增加如下内容<br>
IPADDR=192.168.226.130   #仅主机模式网段<br>
NETMASK=255.255.255.0<br>
重启网络：systemctl restart network<br>

### 2、配置cinder存储<br>
虚拟机上的60GB硬盘在本实验中为 sdb<br>
pvcreate /dev/sdb<br>
vgcreate cinder-volumes /dev/sdb<br>

### 3、配置加速源<br>
yum 加速源(centos7 阿里源)<br>
yum install -y wget<br>
mv /etc/yum.repos.d/CentOS-Base.repo /etc/yum.repos.d/CentOS-Base.repo.backup<br>
wget -O /etc/yum.repos.d/CentOS-Base.repo http://mirrors.aliyun.com/repo/Centos-7.repo<br>
wget -O /etc/yum.repos.d/epel.repo http://mirrors.aliyun.com/repo/epel-7.repo<br>
yum clean all<br>
yum makecache<br>
### 4、pip 加速源(阿里源)<br>
mkdir ~/.pip<br>
cat > ~/.pip/pip.conf << EOF <br>
[global]<br>
trusted-host=mirrors.aliyun.com<br>
index-url=https://mirrors.aliyun.com/pypi/simple/<br>
EOF<br>
### 5、docker 加速源（阿里源）<br>
mkdir /etc/docker<br>
cat > /etc/docker/daemon.json << EOF<br>
{<br>
  "registry-mirrors": ["https://jzngeu7d.mirror.aliyuncs.com"]<br>
}<br>
EOF<br>
### 6、配置iptables<br>
yum install iptables -y<br>
yum install iptables-services -y<br>
systemctl start iptables.service<br>
systemctl enable iptables.service<br>

iptables -F<br>
iptables -P INPUT ACCEPT<br>
iptables -P OUTPUT ACCEPT<br>
iptables -P FORWARD ACCEPT<br>
service iptables save<br>
systemctl restart iptables.service<br>
至此基础环境准备完成。<br>

### 7、kolla-ansible 部署<br>
#### 7.1、安装软件环境<br>
yum install -y epel-release <br>
yum install -y python-pip<br>
pip install -U pip<br>
yum install -y python-devel libffi-devel gcc openssl-devel libselinux-python<br>
yum install -y ansible<br>
pip install -U ansible<br>
编辑ansible配置文件，在defaults中添加3个属性<br><br>
vim /etc/ansible/ansible.cfg<br>
[defaults]<br>
host_key_checking=False<br>
pipelining=True<br>
forks=100<br>
#### 7.2、安装 kolla<br>
pip install kolla-ansible==7.0.0<br>
cp -r /usr/share/kolla-ansible/etc_examples/kolla /etc/<br>
cp /usr/share/kolla-ansible/ansible/inventory/* /opt/<br>
#### 7.3、配置主要文件<br>
这里有4个文件，简单介绍：<br>
•	/etc/kolla/globals.yml 决定要装什么组件和openstack基础配置<br>
•	/etc/kolla/passwords.yml 可以定义openstack各组件密码<br>
•	/opt/all-in-one 决定openstack组件安装得物理位置<br>
•	/opt/multinode 决定openstack组件安装得物理位置<br>
#### 7.4、开始配置：<br>
对于passwords.yml：<br>
kolla-genpwd，这命令生成随机码作为密码使用，可以更改keystone_admin=123456，方便自己登陆。<br>
对于globals.yml：<br>
此文件包含两部分内容：openstack基础配置，选择安装的openstack组件。<br>
vim /etc/kolla/globals.yml <br>
kolla_base_distro: "centos"  # 基础容器镜像版本<br>
kolla_install_type: "source"  # 源码安装方式安装组件<br>
openstack_release: "queens"  # openstack版本，选择你需要的<br>
network_interface: "ens35"  # 管理网使用的网卡<br>
neutron_external_interface: "ens34"  # public网使用得网卡<br>
kolla_internal_vip_address: "192.168.226.131"  # 服务内部地址。<br>
kolla_external_vip_address: "192.168.159.131"  # 服务外部地址。<br>
enable_cinder: "yes"<br>
enable_cinder_backend_lvm: "yes"<br>
cinder_volume_group: "cinder-volumes"<br>
enable_horizon: "yes"<br>
nova_compute_virt_type=qemu<br>

### 8、开始部署<br>
kolla-ansible -i /opt/all-in-one bootstrap-servers<br>
kolla-ansible -i /opt/all-in-one prechecks<br>
kolla-ansible -i /opt/all-in-one deploy<br>
### 9、基本使用<br>
安装命令行工具：<br>
pip install python-openstackclient python-glanceclient python-neutronclient<br>
确认部署（会生成管理员密码等）：<br>
kolla-ansible post-deploy<br>
导入环境变量：<br>
source /etc/kolla/admin-openrc.sh<br>
查看服务状态：<br>
openstack service list --long<br>
至此openstack基本环境以及搭建完成。<br>

