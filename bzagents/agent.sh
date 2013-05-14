read -p "Input port number: " port
python -u pathfindingagent.py localhost $port | gnuplot -p
