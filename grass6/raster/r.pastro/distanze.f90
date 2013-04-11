program distanze
implicit none

integer::i,j,k
real::a,dist
real(kind=8),allocatable::prof(:,:),plot(:,:)

open(10,FILE='./per_plot2',STATUS='OLD')
open(11,FILE='./per_plot3',STATUS='OLD')
open(12,FILE='./info_sentiero',STATUS='OLD')
!open(13,FILE='./sentiero.txt',STATUS='OLD')

k=0
do
   read(10,*,end=100)a
   k=k+1
end do
100 allocate(prof(k,4))
allocate(plot(k,4))
rewind(10)
do i=1,k
   read(10,*)(prof(i,j),j=1,4)
end do
do i=1,k
   plot(i,2)=prof(i,3)
end do
plot(1,1)=0
do i=2,k
   dist=sqrt((prof(i,1)-prof(i-1,1))**2+(prof(i,2)-prof(i-1,2))**2)
   plot(i,1)=plot(i-1,1)+dist
   plot(i,3)=(plot(i,2)-plot(i-1,2))/dist
   ! colonna dove calcolo la velocita in km/h (aggiunta roberto, da mettere in python)
   !plot(i,4)=3.6*dist/(prof(i,4)-prof(i-1,4))
end do
!file per grafico
do i=1,k
   write(11,*)(plot(i,j),j=1,2)
end do

!file per re-importazione in GRASSS con le velocita'
!do i=1,k
!   write(13,*)prof(i,1),prof(i,2),prof(i,3),plot(i,4)
!end do

! preparazione di un file informativo di output
write(12,*)
write(12,*)'---------------------------------------------'
write(12,*)
write(12,'(A17,I5,A14)')'  Tempo stimato: ',int(prof(k,4)/60),' minuti circa.'
write(12,*)
write(12,'(A22,F5.1,A9)')'  Lunghezza percorso: ',plot(k,1)/1000,' km circa.'
write(12,*)
write(12,'(A20,I4,A7)')'  Pendenza massima: ',int(max(abs(maxval(plot(:,3))),abs(minval(plot(:,3))))*100),'% circa.'
write(12,*)
write(12,*)'---------------------------------------------'
write(12,*)
close(12)

end
