
module dd
integer,parameter::ferma_bisezione=15
integer::n_no_null
real, allocatable, dimension(:)::val, iind, jind
real::output
end module dd


!*******************************************************************************************************************************************************
!il programma controlla quelle aree che il precedente programma fortran aveva pulito tenendo in conto la presenza di argini
!l'acqua infatti può arrivare al di là degli argini anche percorrendo percorsi NON ortogonali all'alveo come si è ivece ipotizzato nei primi 2 step
!in particolare l'acqua può seguire alcuni percorsi secondo la massima pendenza---> a tale scopo si è precedentemente creato un reticolo
!il programma per ogni pixel == 1 della matrice diff_inond_2 cerca il punto del reticolo2d più vicino
!quindi percorre il tratto tra il pixel e il reticolo
!se incontra DTM più alto o punto asciutto---> pixel==0
!in caso contrario ----> pixel=1
! a tale scopo utilizza in input:  - il file contenente i limiti della regione
!                                  - il file contenente la matrice diff_inond 
!                                  - il DTM
!                                  - i file contenente i punti del reticolo
!fornisce in output per il profilo considerato una matrice con le aree da inondare nuovamente che poi andrà sommata alla carta di inondazione
!*******************************************************************************************************************************************************


program correzione_punti
use dd
implicit none

real:: nord, sud, ovest, est
integer,parameter::punti=15
integer::i,j, ii, iii, f, iend, righe, colonne, pixel_temp_i, pixel_temp_j, npunti, caso, righe2,colonne2
integer, allocatable, dimension(:,:):: diff_inond, pixel_inondati
!real, allocatable, dimension(:,:)::  punti3d
real(kind=8)::x, temp, dist_min, dist_temp, E_pixel, N_pixel, E_t, N_t, res2, res
real(kind=8),dimension(punti)::dist, EE, NN,qq
real, allocatable, dimension(:):: E, N, quota
character(len=40)::xx, tab, tab1
character(40)::nomefile1,nomefile2,nomefile3,nomefile4,nomefile5,nomefile6
open(unit=40, status='old', file='nomefile.txt')
read(40,*)nomefile1,nomefile2,nomefile3,nomefile4,nomefile5,nomefile6
close(40)


!50 region10.txt
!51 diff_inond
!   dtm2x2 nomefile5 (vd dopo)
!55 punti3d_reticolo
!54 region2.txt
!60 correzione

open(unit=50, status='old', file=nomefile4)
open(unit=51, status='old', file=nomefile1)
!open(unit=52, status='old', file='grass_script/dtm2x2')
open(unit=55, status='old', file=nomefile2)
open(unit=54, status='old', file=nomefile6)
open(unit=60, file=nomefile3)


!leggo le dimensioni della regione utili per allocare le matrici in cui memorizzare carta di input e di output
do i=1,13
   read(50,*)xx
   if (xx=='north:') then
      backspace(50) 
      read(50,*)xx, nord
      write(60,'(a6,f10.2)') trim(xx), nord
      !write(60,'(a6,i)') trim(xx), nord
      !write(60,*) trim(xx), nord
 else if (xx=='nsres:') then
      backspace(50) 
      read(50,*)xx, res
   else if (xx=='south:') then
      backspace(50) 
      read(50,*)xx, sud
      write(60,'(a6,f10.2)')trim(xx), sud
      !write(60,*) trim(xx), sud
   else if (xx=='east:') then
      backspace(50) 
      read(50,*)xx, est
      write(60,'(a5,f10.2)') trim(xx), est
      !write(60,*) trim(xx), est
   else if (xx=='west:') then
      backspace(50) 
      read(50,*)xx, ovest
      write(60,'(a5,f10.2)')trim(xx), ovest
      !write(60,*) trim(xx), ovest
   else if (xx=='rows:') then
      backspace(50)  
      read(50,*)xx, righe
      write(60,'(a5,i5)')trim(xx), righe
      !write(60,*) trim(xx), righe
   else if (xx=='cols:') then
      backspace(50) 
      read(50,*)xx, colonne
      write(60,'(a5,i5)')trim(xx), colonne
      !write(60,*) trim(xx), colonne
   endif
enddo
write(6,*) nord, sud, est, ovest, righe, colonne,res
rewind(50)
close(50)


allocate(diff_inond(righe,colonne))
allocate(pixel_inondati(righe,colonne))
!allocate(punti3d(righe,colonne))

!leggo la matrice diff_inond 
read(51,*) ((diff_inond(i,j), j=1,colonne), i=1,righe)
write(6,*) 'Read raster map of areas to control'
rewind(51)
close(51)

do i=1,13
   read(54,*)xx
   if (xx=='nsres:') then
      backspace(54) 
      read(54,*)xx, res2
      res2=int(res2)
   else if (xx=='rows:') then
      backspace(54)  
      read(54,*)xx, righe2
   else if (xx=='cols:') then
      backspace(54) 
      read(54,*)xx, colonne2
   endif
enddo
write(6,*) righe2, colonne2,res2
rewind(54)
close(54)
!allocate(quota_terreno(righe2,colonne2))

!leggo il DTM
!read(52,*) ((quota_terreno(i,j), j=1,colonne2), i=1,righe2)
!write(6,*) 'letto il DTM'
!rewind(52)
!close(52)
call matrice_sparsa (nomefile5,righe2,colonne2)
write(6,*) 'Read the Digital Terrain Model with Compressed Sparse Rows algorithm'


!scrivo 0 sulla matrice di output
do j=1,colonne
   do i=1,righe
      pixel_inondati(i,j)=0
   enddo
enddo

!guardo quant'è lungo il file che contiene i punti
do i=1,10000000
   read(55,*,iostat=iend)xx
   if(iend /= 0)exit
enddo
if(iend > 0)then
   write(6,*)'Error reading points of course by each river section:',iend
   stop
endif
npunti=i-1
write(6,*) 'There are',npunti,' of water course by each river section to analize'
rewind(55)


allocate(E(npunti))
allocate(N(npunti))
allocate(quota(npunti))


!call modifica_ascii(npunti)

!open(unit=55,status='old',file='punti_mod')

do i=1,npunti
   read(55,*) E(i), N(i), quota(i)
   !write(6,*) i, E(i), N(i), quota(i)
enddo
!write(6,*) 'fatto per oggi basta!!!'


j=0
i=0
1000 j=j+1
1001 i=i+1
!write(6,*)i,j
if(i==righe+1) then
   if(j==colonne)then
      go to 1111
   endif
   i=0
   go to 1000
endif
if(diff_inond(i,j)==1) then
   !write(6,*)i,j
   E_pixel=ovest+res*j-res/2
   N_pixel=nord-(res*i-res/2)
   dist_min=1000000000000000000.
   !bisogna cercare i punti (il numero è 1 paramatro del programma) più vicini a detto pixel
   !quindi si esegue un controllo sul percorso pixel punto
   !se la quota del dtm è sempre inferiore a quella idraulica -->pixel a rischio
   !se la quota del dtm fosse maggiore --> si passa a vedere il percorso dal punto "i+1 -esimo"
   !conclusi i punti se il dtm è sempre + elevato ---> pixel non a rischio
   do ii=1,punti-1
      dist(ii)=0.
      EE(ii)=E(ii)
      NN(ii)=N(ii)
      qq(ii)=quota(ii)
   enddo
   do ii=1,npunti
      dist_temp=sqrt((E(ii)-E_pixel)**2.+(N(ii)-N_pixel)**2.)
      if (dist_temp<dist_min)then
         do iii=punti,2,-1
            dist(iii)=dist(iii-1)
            EE(iii)=EE(iii-1)
            NN(iii)=NN(iii-1)
            qq(iii)=qq(iii-1)
         enddo
         dist(1)=dist_temp
         EE(1)=E(ii)
         NN(1)=N(ii)
         qq(1)=quota(ii)
         dist_min=dist_temp
      endif
   enddo
   !se la distanza è < della semidiagonale del pixel allora vuol dire che siamo nel pixel dove si trova il reticolo --> a rischio
   if (dist(1)<res*sqrt(2.)/2) then
       pixel_inondati(i,j)=1
       go to 1001
   endif  
   x=res2
   caso=0
1003 caso=caso+1
   E_t=EE(caso)
   N_t=NN(caso)
  ! write(6,*)E_t, N_t,x
   temp=0.
   1002 temp=temp+x
   !write(6,*)temp, dist(caso)
   E_t=E_t+x*(E_pixel-EE(caso))/dist(caso)
   N_t=N_t+x*(N_pixel-NN(caso))/dist(caso)
   pixel_temp_i=1+int((nord-N_t)/res2)
   pixel_temp_j=1+int((E_t-ovest)/res2)
   if(temp>dist(caso))then
      pixel_inondati(i,j)=1
      !write(6,*)'1', i,j
      go to 1001
   endif
  ! if (pixel_temp_j==0)then
   !   write(6,*) i, j, caso,x, temp, dist(caso), E_t, EE(caso),E_pixel, N_t, NN(caso), N_pixel
    !  stop
 !  endif
   call trova_elemento(pixel_temp_i,pixel_temp_j)
   if(qq(caso)<=output)then
      pixel_inondati(i,j)=0
      !write(6,*)i,j,quota_terreno(pixel_temp_i,pixel_temp_j),quota(caso),'0'
      if(caso<punti)then
         go to 1003
      endif
      go to 1001
   else
      go to 1002
   endif
else 
   go to 1001
endif

1111 write(6,*)'End of computational steps → writing output raster map'


!scrivo la matrice dei risultati
write(60,*)  ((pixel_inondati(i,j), j=1,colonne), i=1,righe)

write(6,*)'END of Fortran Code → OK'
end program correzione_punti






!*******************************************************************************************************************************************************
!subroutine per modificare il file ascii
!*******************************************************************************************************************************************************
subroutine modifica_ascii(ferma)
implicit none
integer::i
integer,intent(IN)::ferma
character(1)::v
character(32)::vvv

write(6,*)ferma

open(unit=54,file='punti_mod')

i=0
10 i=i+1
if(i==ferma+1)then 
   write(6,*) 'Stop', ferma
   go to 11
endif
read(53,*)vvv
!write(6,*)vvv,i
if (vvv(7:7)=='|')then 
   if (vvv(15:15)=='|') then
      if(vvv(22:22)=='|')then
         write(54,*)vvv(1:6), ' ', vvv(8:14), ' ', vvv(16:21)
         go to 10
      else if (vvv(17:17)=='|')then
         write(54,*)vvv(1:6), ' ', vvv(8:14), ' ', vvv(16:16)
         go to 10
      else if (vvv(18:18)=='|')then
         write(54,*)vvv(1:6), ' ', vvv(8:14), ' ', vvv(16:17)
         go to 10
      else if (vvv(19:19)=='|')then
         write(54,*)vvv(1:6), ' ', vvv(8:14), ' ', vvv(16:18)
         go to 10
      else if (vvv(20:20)=='|') then
         write(54,*)vvv(1:6), ' ', vvv(8:14), ' ', vvv(16:19)
         go to 10
      else if (vvv(21:21)=='|') then
         write(54,*)vvv(1:6), ' ', vvv(8:14), ' ', vvv(16:20)
         go to 10
      else if (vvv(23:23)=='|') then
         write(54,*)vvv(1:6), ' ', vvv(8:14), ' ', vvv(16:22)
         go to 10  
      endif
   else if(vvv(17:17)=='|') then
      if (vvv(24:24)=='|')then
         write(54,*)vvv(1:6), ' ', vvv(8:16), ' ', vvv(18:23)
         go to 10
      else if (vvv(19:19)=='|')then
         write(54,*)vvv(1:6), ' ', vvv(8:16), ' ', vvv(18:18)
         go to 10
      else if (vvv(20:20)=='|')then
         write(54,*)vvv(1:6), ' ', vvv(8:16), ' ', vvv(18:19)
         go to 10
      else if (vvv(21:21)=='|')then
         write(54,*)vvv(1:6), ' ', vvv(8:16), ' ', vvv(18:20)
         go to 10
      else if (vvv(22:22)=='|')then
         write(54,*)vvv(1:6), ' ', vvv(8:16), ' ', vvv(18:21)
         go to 10
      else if (vvv(23:23)=='|')then
         write(54,*)vvv(1:6), ' ', vvv(8:16), ' ', vvv(18:22)
         go to 10
      else if (vvv(25:25)=='|')then
         write(54,*)vvv(1:6), ' ', vvv(8:16), ' ', vvv(18:24)
         go to 10
      endif
   else if(vvv(18:18)=='|') then
      if (vvv(20:20)=='|')then
         write(54,*)vvv(1:6), ' ', vvv(8:17), ' ', vvv(19:19)
         go to 10
      else if (vvv(21:21)=='|')then
         write(54,*)vvv(1:6), ' ', vvv(8:17), ' ', vvv(19:20)
         go to 10
      else if (vvv(22:22)=='|')then
         write(54,*)vvv(1:6), ' ', vvv(8:17), ' ', vvv(19:21)
         go to 10
      else if (vvv(23:23)=='|')then
         write(54,*)vvv(1:6), ' ', vvv(8:17), ' ', vvv(19:22)
         go to 10
      else if (vvv(24:24)=='|')then
         write(54,*)vvv(1:6), ' ', vvv(8:17), ' ', vvv(19:23)
         go to 10
      else if (vvv(25:25)=='|')then
         write(54,*)vvv(1:6), ' ', vvv(8:17), ' ', vvv(19:24)
         go to 10
      else if (vvv(26:26)=='|')then
         write(54,*)vvv(1:6), ' ', vvv(8:17), ' ', vvv(19:25)
         go to 10     
      endif
   endif
   
   
else if (vvv(9:9)=='|')then 
   if (vvv(17:17)=='|') then
      if (vvv(24:24)=='|')then
         write(54,*)vvv(1:8), ' ', vvv(10:16), ' ', vvv(18:23)
         go to 10
      else if (vvv(19:19)=='|')then
         write(54,*)vvv(1:8), ' ', vvv(10:16), ' ', vvv(18:18)
         go to 10
      else if (vvv(20:20)=='|')then
         write(54,*)vvv(1:8), ' ', vvv(10:16), ' ', vvv(18:19)
         go to 10
      else if (vvv(21:21)=='|')then
         write(54,*)vvv(1:8), ' ', vvv(10:16), ' ', vvv(18:20)
         go to 10
      else if (vvv(22:22)=='|')then
         write(54,*)vvv(1:8), ' ', vvv(10:16), ' ', vvv(18:21)
         go to 10
      else if (vvv(23:23)=='|')then
         write(54,*)vvv(1:8), ' ', vvv(10:16), ' ', vvv(18:22)
         go to 10
      else if (vvv(25:25)=='|')then
         write(54,*)vvv(1:8), ' ', vvv(10:16), ' ', vvv(18:24)
         go to 10
      endif
   else if(vvv(19:19)=='|') then
      if (vvv(21:21)=='|') then
         write(54,*)vvv(1:8), ' ', vvv(10:18), ' ', vvv(20:20)
         go to 10
      else if (vvv(22:22)=='|') then
         write(54,*)vvv(1:8), ' ', vvv(10:18), ' ', vvv(20:21)
         go to 10
      else if (vvv(23:23)=='|') then
         write(54,*)vvv(1:8), ' ', vvv(10:18), ' ', vvv(20:22)
         go to 10
      else if (vvv(24:24)=='|') then
         write(54,*)vvv(1:8), ' ', vvv(10:18), ' ', vvv(20:23)
         go to 10
      else if (vvv(25:25)=='|') then
         write(54,*)vvv(1:8), ' ', vvv(10:18), ' ', vvv(20:24)
         go to 10
      else if (vvv(26:26)=='|') then
         write(54,*)vvv(1:8), ' ', vvv(10:18), ' ', vvv(20:25)
         go to 10
      else if (vvv(27:27)=='|') then
         write(54,*)vvv(1:8), ' ', vvv(10:18), ' ', vvv(20:26)
         go to 10
      endif
   else if(vvv(20:20)=='|') then
      if(vvv(22:22)=='|') then
         write(54,*)vvv(1:8), ' ', vvv(10:19), ' ', vvv(21:21)
         go to 10
      else if (vvv(23:23)=='|')then
         write(54,*)vvv(1:8), ' ', vvv(10:19), ' ', vvv(21:22)
         go to 10
      else if (vvv(24:24)=='|')then
         write(54,*)vvv(1:8), ' ', vvv(10:19), ' ', vvv(21:23)
         go to 10
      else if (vvv(25:25)=='|')then
         write(54,*)vvv(1:8), ' ', vvv(10:19), ' ', vvv(21:24)
         go to 10
      else if  (vvv(26:26)=='|') then
         write(54,*)vvv(1:8), ' ', vvv(10:19), ' ', vvv(21:25)
         go to 10
      else if  (vvv(27:27)=='|') then
         write(54,*)vvv(1:8), ' ', vvv(10:19), ' ', vvv(21:26)
         go to 10
      else if  (vvv(28:28)=='|') then
         write(54,*)vvv(1:8), ' ', vvv(10:19), ' ', vvv(21:27)
         go to 10
      endif
   endif


else if (vvv(10:10)=='|')then
   if(vvv(18:18)=='|') then
      if (vvv(20:20)=='|')then
         write(54,*)vvv(1:9), ' ', vvv(11:17), ' ', vvv(19:19)
         go to 10
      else  if (vvv(21:21)=='|')then
         write(54,*)vvv(1:9), ' ', vvv(11:17), ' ', vvv(19:20)
         go to 10
      else if (vvv(22:22)=='|')then
         write(54,*)vvv(1:9), ' ', vvv(11:17), ' ', vvv(19:21)
         go to 10
      else if (vvv(23:23)=='|')then
         write(54,*)vvv(1:9), ' ', vvv(11:17), ' ', vvv(19:22)
         go to 10
      else if (vvv(24:24)=='|')then
         write(54,*)vvv(1:9), ' ', vvv(11:17), ' ', vvv(19:23)
         go to 10
      else if (vvv(25:25)=='|')then
         write(54,*)vvv(1:9), ' ', vvv(11:17), ' ', vvv(19:24)
         go to 10
      else if (vvv(26:26)=='|')then
         write(54,*)vvv(1:9), ' ', vvv(11:17), ' ', vvv(19:25)
         go to 10     
      endif
   else if (vvv(20:20)=='|') then
      if(vvv(22:22)=='|') then
         write(54,*)vvv(1:9), ' ', vvv(11:19), ' ', vvv(21:21)
         go to 10
      else if (vvv(23:23)=='|')then
         write(54,*)vvv(1:9), ' ', vvv(11:19), ' ', vvv(21:22)
         go to 10
      else if (vvv(24:24)=='|')then
         write(54,*)vvv(1:9), ' ', vvv(11:19), ' ', vvv(21:23)
         go to 10
      else if (vvv(25:25)=='|')then
         write(54,*)vvv(1:9), ' ', vvv(11:19), ' ', vvv(21:24)
         go to 10
      else if  (vvv(26:26)=='|') then
         write(54,*)vvv(1:9), ' ', vvv(11:19), ' ', vvv(21:25)
         go to 10
      else if  (vvv(27:27)=='|') then
         write(54,*)vvv(1:9), ' ', vvv(11:19), ' ', vvv(21:26)
         go to 10
      else if  (vvv(28:28)=='|') then
         write(54,*)vvv(1:9), ' ', vvv(11:19), ' ', vvv(21:27)
         go to 10
      endif
   else if (vvv(21:21)=='|') then
      if(vvv(23:23)=='|')then
         write(54,*)vvv(1:9), ' ', vvv(11:20), ' ',vvv(22:22)
         go to 10
      else  if(vvv(24:24)=='|')then
         write(54,*)vvv(1:9), ' ', vvv(11:20), ' ',vvv(22:23)
         go to 10
      else  if(vvv(25:25)=='|')then
         write(54,*)vvv(1:9), ' ', vvv(11:20), ' ',vvv(22:24)
         go to 10
      else  if(vvv(26:26)=='|')then
         write(54,*)vvv(1:9), ' ', vvv(11:20), ' ',vvv(22:25)
         go to 10
      else  if(vvv(27:27)=='|')then
         write(54,*)vvv(1:9), ' ', vvv(11:20), ' ',vvv(22:26)
         go to 10
      else  if(vvv(28:28)=='|')then
         write(54,*)vvv(1:9), ' ', vvv(11:20), ' ',vvv(22:27)
         go to 10
      else if(vvv(29:29)=='|')then
         write(54,*)vvv(1:9), ' ', vvv(11:20), ' ',vvv(22:28)
         go to 10
      endif
   endif
   go to 10
endif

11 close(53)
close(54)

end subroutine modifica_ascii





!************************************************************************************************
!Subroutine allocazione matrice sparsa
!************************************************************************************************

subroutine matrice_sparsa (nomefile,righe,colonne)
!uso l'algoritmo CSR(Compressed               )
use dd
implicit none
character(40)::nomefile
integer::i,j, cont, righe,colonne, nn, cont2
real::a
real,allocatable,dimension(:):: temp


allocate(temp(colonne))
allocate (iind(righe+1))
open (unit=70, file=nomefile)
cont=0

do i=1,righe
   read(70,*)(temp(j), j=1,colonne)
   !write(6,*) temp
   do j=1,colonne
      if (temp(j)/=0.) then 
         cont=cont+1
      endif
   enddo
enddo
rewind(70)

n_no_null=cont
write(6,*)'There are', n_no_null, ' no-null cells in the Digital Terrain Model'

allocate (val(n_no_null))
allocate (jind(n_no_null))


cont=0
cont2=0
do i=1,righe
   cont2=cont+1
   iind(i)=cont2
   read (70,*) (temp(j),j=1,colonne)
   do j=1,colonne
      if (temp(j)/=0.) then 
         cont=cont+1	
         val(cont)=temp(j)
         jind(cont)=j	
      endif
   enddo
enddo
iind(righe+1)=n_no_null+1

!write(6,*) "val=", val
!write(6,*) "iind=", iind
!write(6,*) "jind=", jind

end subroutine matrice_sparsa





!************************************************************************************************
!Subroutine trova punto in matrice sparsa
!************************************************************************************************

subroutine trova_elemento(iriga,jcolonna)
use dd
integer::i,iriga,jcolonna, iniz, fine

iniz=iind(iriga)
fine=iind(iriga+1)-1

do i=iniz,fine
   if (jind(i)==jcolonna)then
      output=val(i)
      go to 144
   else
      output=0.
   endif
enddo

144 i=0

end subroutine trova_elemento
