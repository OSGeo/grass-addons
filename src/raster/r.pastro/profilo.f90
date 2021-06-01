program profilo
implicit none

integer::i,j,k
real::a,dist
real(kind=8),allocatable::prof(:,:),plot(:,:)

open(8,FILE='./profilo_N',STATUS='OLD')
open(9,FILE='./profilo_E',STATUS='OLD')
open(10,FILE='./profilo_h',STATUS='OLD')
open(11,FILE='./profilo_costo',STATUS='OLD')
open(12,FILE='./per_plot',STATUS='OLD')
k=0
do
   read(8,*,end=100)a
   k=k+1
end do
100 allocate(prof(k,4))
allocate(plot(k,2))
rewind(8)
do i=1,k
   read(8,*)prof(i,1)
   read(9,*)prof(i,2)
   read(10,*)prof(i,3)
   read(11,*)prof(i,4)
end do
do i=2,k
   write(12,'(F12.3,2X,F12.3,2X,F12.3,2X,F12.3)')prof(i,1),prof(i,2),prof(i,3),prof(i,4)
end do

end
