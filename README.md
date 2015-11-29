# event

* http://www.solutionscop21.org/
* 4-10 December 2015
* Grand Palais, Paris, France

# description

## Un réseau de capteurs pour monitorer le manteau neigeux

Lorsque la neige fond, il est important de savoir où l'eau va pour prédire le remplissage des nappes phréatiques, la production des barrages hydroélectriques, prévoir les périodes de sècheresse... C'est ce que fait l'équipe EVA à Inria en collaboration avec l'équipe du Prof. Glaser à l'université de Californie à Berkeley. Ils ont déployé 945 capteurs dans la Sierra Nevada, montés sur des mats (voir ci-contre) qui mesurent la hauteur de neige. Sur l'écran, vous pouvez voir le même réseau déployé ici au Grand Palais, et qui mesure la température. Flashez le code QR pour voir les données sur votre téléphone!

## A Wireless Sensor Network to Monitor the Snowmelt Process

It's important to know where the water goes when the snow melt, as it allow to predict how much groundwater there will be available, how much a hydroelectric plant will produce, whether some region might face draught... The Inria EVA team in collaboration with Prof. Glaser's team at UC Berkeley have deployed 945 sensors throughout the Sierra Nevada do to just that. Sensors which measure snow depth are mounted on poles (see above). On the screen you can see the same type of network deployed right here in the Grand Palais, and which monitors temperature. Scan the QR code on the left to see the live data on your phone!

# configure the network

To enter these commands:
* connect to the device (either manager - yellow sticker - or mote - white sticker)
* open the Windows devices manager to see the 4 COM ports create (e.g. COM2,COM3,COM4,COM5)
* Using PuTTY (http://www.chiark.greenend.org.uk/~sgtatham/putty/download.html) open the 3rd (e.g. COM4 above) COM port with default serial settings

## manager commands

To change the netid:

```
> set config netid 425
```

To see the nodes connected:

```
> sm
```

To ping a mote:

```
> ping 2
```

## mote commands

```
mset netid 425
```

# install/run the application

* download Python 2.7 (NOT Python 3) from https://www.python.org/downloads/
* download this repo (https://github.com/twatteyne/SolutionsCOP21) using "Download ZIP" on the right
* unzip
* open an command promt and navigate to the `SolutionsCOP21/software/` of this code
* type:
```
> C:\Python27\Scripts\pip.exe install -r requirements.txt
```
* make sure the computer is connected to the Internet
* edit `SolutionsCOP21\software\bin\SolutionsCOP21\static\dashboard.js`, variable positions with the 15 MAC addresses of your motes. The MAC address of any mote/manager starts with `00-17-0d-00-00`, the final 3 bytes are printed on the little label of the mote
* let me knpw what those are, so I can update the public site (see below)
* in `SolutionsCOP21\software\bin\SolutionsCOP21\SolutionsCOP21.py`, change `COM9` (bottom of the file) for the 4th COM port in your device manager
* start the application by double-clicking on `SolutionsCOP21/software/bin/SolutionsCOP21/SolutionsCOP21.py`

# what to expect

* the command prompt you start stays empty, except when errors occur
* start a browser on the machine you run the program on, go to http://127.0.0.1:8080/. You see the map+temperature+topology
* from any computer, go to http://dustcloud.github.io/dashboard_dust/. You see the map+temperature (NO topology, that's normal)