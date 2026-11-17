# 이 파일을 더블클릭하면 콩이가 나와요. (Python 필요)
import os, runpy, sys
here = os.path.dirname(os.path.abspath(__file__))
os.chdir(here)
sys.path.insert(0, here)
runpy.run_path(os.path.join(here, "pet.py"), run_name="__main__")
