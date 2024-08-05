import time
import sys
import threading
import os
import sys

fruits = ["Apple", "Banana", "Cherry", "Blackberries", "Clementine", "Figs", "Mango", "Nectarine", "Pineapple", "Strawberries", "Watermelon", "Tangerine"]

def _read_stdin():
  for line in sys.stdin:
      print("stdin echo:", line)
      # stop when we receive 'exit' or 'quit'
      if 'exit' == line.rstrip().lower() or 'quit' == line.rstrip().lower():
          break

def main():
  print('Number of arguments:', len(sys.argv), 'arguments.')
  print('Argument List:', str(sys.argv)) 
  print('Evironment:\n') 
  print(os.environ, '\n')
  t = threading.Thread(name='stdin_thread', target=_read_stdin)
  t.start()
  
  while t.is_alive():
    for f in fruits:
      print(f)
      time.sleep(1)
      if not t.is_alive():
        break
        
if __name__ == "__main__":
    main()

