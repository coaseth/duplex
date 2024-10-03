apt install locate
apt install mc
apt install python3
apt install python3.12-venv

---\environment activation/---
python3 -m venv lasram-duplex;
source lasram-duplex/bin/activate

---\Script/---
/home/lasram-duplex/lasram-duplex/gcodekonverter

---\Site-Packages/---
/home/lasram-duplex/lasram-duplex/gcodekonverter/lasram-duplex/lib/python3.12/site-packages/gcode2as

---\Generalo/---
file generalo.sh #megnézni hogy mi van vele
Generalo.sh: Python script, ASCII text executable, with CRLF line terminators

sed -i 's/\r$//' Generalo.sh

file Generalo.sh
Generalo.sh: Python script, ASCII text executable

RUN:
{script path} {filename} {output directory}

./Generalo.sh /home/lasram-duplex/lasram-duplex/gcodekonverter/Shape-Box_dupl.stl /home/lasram-duplex
