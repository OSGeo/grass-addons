lgrind -e docu.lg > docu_ispecunmix.tex
#latex docu_ispecunmix.tex
rm -rf OBJ.linux statistics.txt *.aux *.log *.idx
mv docu_ispecunmix.tex ../..
