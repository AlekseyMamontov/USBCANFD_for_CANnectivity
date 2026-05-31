

<img src="https://cannectivity.org/_static/CANnectivity.png" width="300" alt="CANnectivity Logo">

Project

https://cannectivity.org/building.html


Github

https://github.com/CANnectivity

Zephyr RTOS  
Version 
<pre>
VERSION_MAJOR = 4
VERSION_MINOR = 4
PATCHLEVEL = 99
VERSION_TWEAK = 0
EXTRAVERSION =
</pre>


https://www.zephyrproject.org/


INSTALL Ubuntu 24.04
------------------------------
<pre>
 
  sudo apt update
 
  apt list --upgradable
 
  sudo apt install python3-pip python3-venv
 
   python3 -m venv .venv
   
   source .venv/bin/activate
   
   pip install --user -U west
   pip install -r zephyr/scripts/requirements.txt
 
 west init -m https://github.com/CANnectivity/cannectivity --mr main my-workspace
 cd my-workspace
 
west update

export ZEPHYR_TOOLCHAIN_VARIANT=gnuarmemb

export GNUARMEMB_TOOLCHAIN_PATH=/usr


</pre>

..


**USB CAN ISO standart**     
<img src="https://github.com/AlekseyMamontov/CANnectivity-CANFD-adapters/blob/main/img/standart072.png" width="200" alt="CANnectivity F072 can-module.com">

<pre>west build -p -b usbcan_iso  cannectivity/app/ -- -DFILE_SUFFIX=release</pre>

**USB CAN FD SOLO  (1 ch)**     

<img src="https://github.com/AlekseyMamontov/CANnectivity-CANFD-adapters/blob/main/img/G431_2.png" width="300" alt="CANnectivity g431 can-module.com">

<pre>west build -p -b usbcanfd_solo_can_module  cannectivity/app/ -- -DFILE_SUFFIX=release</pre>




**USB CAN FD DUAL  (2ch)**   

<img src="https://github.com/AlekseyMamontov/CANnectivity-CANFD-adapters/blob/main/img/G473.png" width="300" alt="CANnectivity g473 can-module.com">

<pre>west build -p -b usbcanfd_dual_can_module  cannectivity/app/ -- -DFILE_SUFFIX=release</pre>



**USB CAN FD TRIO  (3 ch)** 

<img src="https://github.com/AlekseyMamontov/CANnectivity-CANFD-adapters/blob/main/img/CanBridge.png" width="300" alt="CANnectivity g473 can-module.com">

<pre>west build -p -b canbridge_g473_can_module  cannectivity/app/ -- -DFILE_SUFFIX=release</pre>



***Linux terminal*** (example usbcanfd dual)

<pre> uname -r </pre>
***if linux kernel < 6.15***
<pre>
 sudo modprobe gs_usb
 echo "1209 ca01" | sudo tee /sys/bus/usb/drivers/gs_usb/new_id
</pre>


<pre>sudo ip link show</pre>

<pre>
32: can0: <NOARP,ECHO> mtu 16 qdisc noop state DOWN mode DEFAULT group default qlen 10
    link/can 
33: can1: <NOARP,ECHO> mtu 16 qdisc noop state DOWN mode DEFAULT group default qlen 10
    link/can 
</pre>

***CAN  500kb  fdata 5Mb*** 
<pre>
sudo ip link set can0 up type can bitrate 500000 dbitrate 5000000 fd on
sudo ip link set can1 up type can bitrate 500000 dbitrate 5000000 fd on
</pre>

***CAN  500kb  fdata 8Mb*** 
<pre>
sudo ip link set can0 up type can bitrate 500000 dbitrate 8000000 fd on
</pre>


<pre>sudo ip link show</pre>

<pre>
32: can0: <NOARP,UP,LOWER_UP,ECHO> mtu 72 qdisc pfifo_fast state UP mode DEFAULT group default qlen 10
    link/can 
33: can1: <NOARP,UP,LOWER_UP,ECHO> mtu 72 qdisc pfifo_fast state UP mode DEFAULT group default qlen 10
    link/can 
</pre>

***Test: generation CANFD packet***
<pre> cangen can0 -f   </pre>
<pre> cangen can1 -f   </pre>


***Force bind gs_usb driver via udev for kernels < 6.15*** 
<pre>
echo 'ACTION=="add", SUBSYSTEM=="usb", ATTRS{idVendor}=="1209", ATTRS{idProduct}=="ca01", RUN+="/sbin/modprobe gs_usb", RUN+="/bin/sh -c \"echo 1209 ca01 > /sys/bus/usb/drivers/gs_usb/new_id\""' | sudo tee /etc/udev/rules.d/99-cannectivity.rules
</pre>
----------------------------
can-module.com
--------------------------

<img src="https://github.com/AlekseyMamontov/CANnectivity-_CANFD-_adapters/blob/main/img/Too_adapters2.jpeg" width="400" alt="USBCANFD 2ch adapter can-module.com">



***3D-printable enclosures for CAN FD adapters (SOLO & DUAL) (freecad, stl, bambulab)***

3DBox_for_adaptersSOLO_DUAL.zip

<img src="https://github.com/AlekseyMamontov/CANnectivity-CANFD-adapters/blob/main/img/Box_CANFD_DUAL_adapter.jpg" width="300" alt="3D-printable enclosures for CAN FD adapters">
<img src="https://github.com/AlekseyMamontov/CANnectivity-CANFD-adapters/blob/main/img/Box_CANFD_DUAL_adapter2.jpg" width="300" alt="3D-printable enclosures for CAN FD adapters">


*CAN Bus Software Overview* 

# SocketCAN, can-utils

<img width="50"  alt="image" src="https://github.com/user-attachments/assets/4599cf1c-6836-4b64-87ad-56a6bc628432" />

https://www.kernel.org/doc/html/latest/networking/can.html

https://github.com/linux-can



# <img src="https://github.com/Schildkroet/CANgaroo/raw/master/src/assets/cangaroo.png" width="48" height="48"> CANgaroo

Schildkroet (https://github.com/Schildkroet/CANgaroo)

This CANgaroo version 0.6.2 works correctly with CANnectivity CAN FD and Candlelight 2.5 FD multichannel adapters using the gs_usb protocol in Windows.

<img width="500"  alt="image" src="https://github.com/user-attachments/assets/8da40527-1ded-48d2-a7d4-de4685cd5034" />




Jayachandran Dharuman (https://github.com/OpenAutoDiagLabs/cangaroo)

<img width="500"  alt="image" src="https://github.com/user-attachments/assets/581d26fd-8e25-40ec-a364-900e12229ea9" />

Wikilift (https://github.com/wikilift/CANgaroo

<img width="500"  alt="image" src="https://github.com/user-attachments/assets/f8424309-0d9e-4b3b-a7cb-6bd4fdba01cb" />

#  SavvyCAN

<img width="500"  alt="image" src="https://github.com/user-attachments/assets/b4a26fa0-ea29-4713-bd0c-ee2b131f507d" />

https://github.com/collin80/SavvyCAN


# <img width="200"  alt="image" src="https://github.com/user-attachments/assets/7878c9a6-fd5d-461f-a3a0-53f5431f9938" />  

https://www.wireshark.org/tools/

<img width="600" alt="image" src="https://github.com/user-attachments/assets/4ab0cf8e-a04c-4f79-9e5e-7fb9f0894ae9" />


# CAN Analyzer

https://github.com/phnahes/can-bus-analyzer

<img width="500"  alt="image" src="https://github.com/user-attachments/assets/09a1846d-35a9-4b4b-a970-f32ae07cef1d" />


<img width="500"  alt="image" src="https://github.com/user-attachments/assets/c630a2d3-ac7f-4b76-a1b5-97889007edbf" />


# 🖥️ RCAN Tools

https://rcantools.com/index.html  
Proprietary commercial software (not open source). SocketCAN native with CAN FD support.

# CANopen lib

https://github.com/CANopenNode

https://github.com/CANopenNode/CANopenEditor

https://github.com/CANopenNode/CanOpenSTM32

https://github.com/CANopenTerm/CANopenTerm

 python-can

https://github.com/hardbyte/python-can
https://github.com/cantools/cantools
https://github.com/canopen-python/canopen CANopen

# QT can-bus-api
https://www.qt.io/blog/qt-can-bus-api-extensions

# more info 
https://github.com/iDoka/awesome-canbus?tab=readme-ov-file#arm


