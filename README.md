Routines de lecture-écriture sur un tag RFID pour des applications en modélisme ferroviaire.
Cette application est destinée à être pilotée via le monitor série (port USB) du RPI Pico.

Une application possible est de détecter un engin (locomotive) par la lecture de sa carte. On peut ainsi récupérer les données utiles comme l'adresse DCC.
La fonction d'écriture permet de stocker sur la carte de nouvelles données.
L'interface peut être manuelle par ligne de commande ou utiliser l'interface graphique écrite en Python/Tkinter et fonctionnant sur un hote (RPI ou PC).

Montage de test :
   + RPI Pico monté sur une platine de test
   + Carte RFID-RC522 montée sur la même platine

Activées :
   + Lecture des tags : Commande READ
   + Ecriture des tags : Commande WRITE suivi de l'ensemble des données à écrire

A faire :
   + On peut envisager transmettre automatiquement les données vers JMRI afin que la nouvelle loco soit prise en charge automatiquement.

Problèmes connus :
