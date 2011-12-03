module dd
integer,parameter::ferma_bisezione=15
integer::n_no_null
real, allocatable, dimension(:)::val, iind, jind
real::output
end module dd

module dati
!****************************************************************************************************************************************
!real, parameter::=2 
!il programma è  pensato per una risoluzione del file raster 2x2 se la risoluzione fosse diversa MODIFICARE  il parametro res
!****************************************************************************************************************************************
real::nord, sud, est, ovest
integer:: righe, colonne, i, j, righe2, colonne2
integer, allocatable, dimension(:,:):: bordi_alveo
real, allocatable, dimension(:,:):: quota_terreno, reticolo2d, inondazioneT
real:: Ebordo, Nbordo, EEE,NNN, zzz, res, res2
end module dati




!****************************************************************************************************************************************
!il programma calcola le direzioni privilegiate dell'acqua al di fuori dell'alveo ottenuto con il precedente modulo trova_alveo.f90
! a tale scopo utilizza in input:  - il file contenente i limiti della regione
!                                  - il file contenente il profilo
!                                  - il file limiti_alveo_vect
!                                  - il DTM
!fornisce in output per il profilo considerato una carta contenente le direzioni privilegiate dell'acqua in base alla massima pendenza
!****************************************************************************************************************************************


program reticolo_2d_fuori_alveo
Use dati
Use dd
implicit none

integer:: ii, f, iend, nrighe, h1, h2, h3, h4, pixel_temp_i, pixel_temp_j 
integer:: nsez, nbordi, nscelta, cont
!integer, allocatable, dimension(:,:):: bordi_alveo
!real, allocatable, dimension(:,:):: quota_terreno
real(kind=8)::E1, E1dopo, N1, N1dopo, quotal, temp, temp1, temp2, z, temp_x, temp_y, E_temp, N_temp, dist
real(kind=8):: num, den, x, y
real(kind=8),dimension(2):: El_ds, El_sx, Nl_ds, Nl_sx
real, allocatable, dimension(:)::profilo, E, N
character(len=40)::xx, tab, tab1,vv
character(40)::nomefile1,nomefile2,nomefile3,nomefile4
character(40)::nomefile5,nomefile6,nomefile7,nomefile8,nomefile9
open(unit=40, status='old', file='nomefile.txt')
read(40,*)nomefile1,nomefile2,nomefile3,nomefile4,nomefile5,& 
nomefile6,nomefile7,nomefile8,nomefile9
close(40)

!50 region20
!51 profilo
!52 dtm20x20'
!53 limiti_alveo_vect
!54 inondazione_step3
!55 region2.txt
!   dtm2x2 nomefile8 (vd dopo)
!60 bordi_alveo
!61 reticolo



open(unit=50, status='old', file=nomefile4)
open(unit=51, status='old', file=nomefile1)
open(unit=52, status='old', file=nomefile5)
open(unit=53, status='old', file=nomefile6)
open(unit=54, status='old', file=nomefile2)
open(unit=55, status='old', file=nomefile7)
!open(unit=56, status='old', file='grass_script/dtm2x2')
open(unit=60, file=nomefile9)
open(unit=61, file=nomefile3)


!leggo le dimensioni della regione utili per allocare le matrici in cui memorizzare carta di input e di output
do i=1,13
   read(50,*)xx
   if (xx=='north:') then
      backspace(50) 
      read(50,*)xx, nord
      !write(60,'(a6,i)') trim(xx), nord
      !write(61,'(a6,i)') trim(xx), nord
     ! write(60,'(a6,f10.2)') trim(xx), nord
      write(61,'(a6,f10.2)') trim(xx), nord
      !write(60,*) trim(xx), nord
      !write(61,*) trim(xx), nord
 else if (xx=='nsres:') then
      backspace(50) 
      read(50,*)xx, res
   else if (xx=='south:') then
      backspace(50) 
      read(50,*)xx, sud
      !write(60,'(a6,f10.2)')trim(xx), sud
      write(61,'(a6,f10.2)')trim(xx), sud
      !write(60,*)trim(xx), sud
      !write(61,*)trim(xx), sud
   else if (xx=='east:') then
      backspace(50) 
      read(50,*)xx, est
      !write(60,'(a5,f10.2)') trim(xx), est
      write(61,'(a5,f10.2)') trim(xx), est
      !write(60,*)trim(xx), est
      !write(61,*)trim(xx), est
   else if (xx=='west:') then
      backspace(50) 
      read(50,*)xx, ovest
      !write(60,'(a5,f10.2)')trim(xx), ovest
      write(61,'(a5,f10.2)')trim(xx), ovest
      !write(60,*)trim(xx), ovest
      !write(61,*)trim(xx), ovest
   else if (xx=='rows:') then
      backspace(50)  
      read(50,*)xx, righe
      !write(60,'(a5,i5)')trim(xx), righe
      write(61,'(a5,i5)')trim(xx), righe
      !write(60,*)trim(xx), righe
      !write(61,*)trim(xx), righe
   else if (xx=='cols:') then
      backspace(50) 
      read(50,*)xx, colonne
      !write(60,'(a5,i5)')trim(xx), colonne
      write(61,'(a5,i5)')trim(xx), colonne
      !write(60,*)trim(xx), colonne
      !write(61,*)trim(xx), colonne
   endif
enddo
write(6,*) nord, sud, est, ovest, righe, colonne,res
rewind(50)
close(50)

allocate(quota_terreno(righe,colonne))
allocate(bordi_alveo(righe,colonne))
allocate(reticolo2d(righe,colonne))

!leggo il DTM
read(52,*) ((quota_terreno(i,j), j=1,colonne), i=1,righe)
write(6,*) "Read the Digital Terrain Model lower resolution"
rewind(52)
close(52)

!scrivo 0 sulla matrice bordi_alveo e reticolo2d
do j=1,colonne
   do i=1,righe
      bordi_alveo(i,j)=0
      reticolo2d(i,j)=0
   enddo
enddo


!guardo quant'è lungo il file che contiene il profilo
do i=1,10000000
   read(51,*,iostat=iend)xx
   if(iend /= 0)exit
enddo
if(iend > 0)then
   write(6,*)'Error reading the file with water surface profile :',iend
   stop
endif
nrighe=i-1
write(6,*) 'The file with water surface profile has',nrighe,' rows'
rewind(51)


!guardo quant'è lungo il file che contiene i bordi sezioni
do i=1,10000000
   read(53,*,iostat=iend)xx
   if(iend /= 0)exit
enddo
if(iend > 0)then
   write(6,*)"Error reading the file with river's boundary:",iend
   stop
endif
nbordi=i-1
write(6,*) "The file with river's boundary has ",nbordi,'rows'
rewind(53)


!leggo le dimensioni della regione utili per allocare le matrici in cui memorizzare carta di input e di output
do i=1,13
   read(55,*)vv
   if (vv=='nsres:') then
      backspace(55) 
      read(55,*)vv, res2
   else if (vv=='rows:') then
      backspace(55)  
      read(55,*)vv, righe2
   else if (vv=='cols:') then
      backspace(55) 
      read(55,*)vv, colonne2
   endif
enddo
write(6,*)  righe2, colonne2,res2
rewind(55)
close(55)


allocate(inondazioneT(righe,colonne))
!allocate(terreno(righe2,colonne2))

!leggo il DTM 2x2
!read(56,*) ((terreno(i,j), j=1,colonne2), i=1,righe2)
!write(6,*)  'letto il DTM'
!rewind(56)
!close(56)

call matrice_sparsa (nomefile8,righe2,colonne2)
write(6,*) "Read the Digital Terrain Model with Compressed Sparse Row (CSR) algorithm"

!leggo la carta inondazione
read(54,*) ((inondazioneT(i,j), j=1,colonne), i=1,righe)
write(6,*)  'Read the raster map of inondation of step 3'
rewind(54)
close(54)





!leggo il file contenente il profilo e se sono nella mia regione traccio delle rette congiungenti i limiti alveo trovati in ogni sezione col precedente modulo
f=0
i=0
cont=0
1000 i=i+1
if (i==nrighe) then
   go to 1001
endif
read(51,*)E1, N1
!write(6,*)i, E1, N1
read(51,*)E1dopo, N1dopo
!write(6,*)i, E1dopo, N1dopo
backspace(51)
if (E1<ovest .or. E1>est .or. N1>nord .or. N1<sud) then
   go to 1000
endif
f=f+1
backspace(51)
read(51,*) E1, N1, z
!write(6,*)cont, i, E1, N1, z
if(cont==nbordi) then
   go to 1000
endif
read(53,*) El_ds(1), Nl_ds(1), quotal, temp1, h1
cont=cont+1
if(cont==nbordi) then
   go to 1000
endif
read(53,*) El_sx(1), Nl_sx(1), quotal, temp1, h2
cont=cont+1
if(cont==nbordi) then
   go to 1000
endif
!1write(6,*)El_ds(1), Nl_ds(1), quotal, temp1, h1,h2
!controllo che ci sia corrispondenza tra il limite alveo a destra e a sinistra (in realtà vale solo per il primo punto)
if(h1/=h2)then
   backspace(53)
   cont=cont-1
   go to 1000  
endif
if(cont==nbordi) then
   go to 1000
endif
123 read(53,*) El_ds(2), Nl_ds(2), quotal,temp,h3
cont=cont+1
if(cont==nbordi) then
   go to 1000
endif
!write(6,*)El_ds(2), Nl_ds(2), quotal,temp,h3
read(53,*) El_sx(2), Nl_sx(2), quotal,temp,h4
cont=cont+1
!write(6,*)cont,  f, El_sx(2), Nl_sx(2), quotal,temp,h3,h4
!controllo che ci sia corrispondenza tra il limite alveo a destra e a sinistra in caso contario "salto quel punto" con attenzione 
if(h3/=h4)then
   backspace(53)
   cont=cont-1
   i=i+1
   f=f+1
   read(51,*) x
   read(51,*) E1dopo, N1dopo
   backspace(51)
   if(cont==nbordi) then
      go to 1000
   endif
   go to 123
   !read(53,*) El_ds(2), Nl_ds(2), quotal,temp,h3
   !cont=cont+1
   !if(cont==nbordi) then
   !   go to 1000
   !endif
   !read(53,*) El_sx(2), Nl_sx(2), quotal,temp,h4
   !cont=cont+1
   !write(6,*) f, El_sx(2), Nl_sx(2), quotal,temp,h3,h4
endif
backspace(53)
cont=cont-1
backspace(53)
cont=cont-1


!ora devo tracciare le varie rette, prima però devo controllare che effettivamente (El_ds(i),Nl_ds(i)) siano entrambe alla destra della centerline
!per fare ciò controllo che il segmento che unisce (E1,N1) a (E1dopo,N1dopo) e quello che unisce i limiti alveo non si incrocino,
!qualora si incrociassero inverto ds(2) e sx(2)
num=N1-(N1dopo-N1)/(E1dopo-E1)*E1-Nl_ds(1)+(Nl_ds(2)-Nl_ds(1))/(El_ds(2)-El_ds(1))*El_ds(1)
den=(Nl_ds(2)-Nl_ds(1))/(El_ds(2)-El_ds(1))-(N1dopo-N1)/(E1dopo-E1)
x=num/den
y=N1+(N1dopo-N1)/(E1dopo-E1)*(x-E1)
!if(f==41)then
!   write(6,*)x,y,E1,N1,E1dopo,N1dopo,El_ds(1),Nl_ds(1),El_ds(2),Nl_ds(2) 
!endif

!write(6,*) num, den, x, y
!guardo se si incrociano
!1/2 
if ( y<=Nl_ds(2) .and.y>=Nl_ds(1) .and. El_ds(1)<=x .and. x<=El_ds(2)) then
   !write(6,*) 'interseca --> correggo1'
   go to 2000
!1\2
else if ( El_ds(1)<=x .and. x<=El_ds(2) .and. Nl_ds(2)<=y .and.  y<=Nl_ds(1)) then
   !write(6,*) 'interseca --> correggo2'
   go to 2000
!2\1
else if (El_ds(2)<=x .and. x<=El_ds(1) .and. y<=Nl_ds(2) .and. y>=Nl_ds(1)) then
   !write(6,*)'interseca --> correggo3'
   go to 2000
!2/1
else if (El_ds(2)<=x .and. x<=El_ds(1) .and. Nl_ds(2)<=y .and. y<=Nl_ds(1)) then
   !write(6,*) 'interseca --> correggo4'
   go to 2000
else
   !write(6,*)'bene'
   go to 2001
endif


2000 temp1=Nl_ds(2)
temp2=Nl_sx(2)
Nl_ds(2)=temp2
Nl_sx(2)=temp1
temp1=El_ds(2)
temp2=El_sx(2)
El_ds(2)=temp2
El_sx(2)=temp1
go to 2001



!a questo punto sono sicuro che i limiti ds e sx siano entrambi dallo stesso lato rispetto alla centerline e procedo col tracciare i bordi dell'alveo
!interpolando linearmente fra 1 punto e il successivo
!DESTRA
2001 write (60,'(a6)')'L  2 1' 
write (60,*)El_ds(1),Nl_ds(1)
write (60,*)El_ds(2),Nl_ds(2)
write (60,*)' 1     1'
dist=sqrt((El_ds(2)-El_ds(1))**2.+(Nl_ds(2)-Nl_ds(1))**2.)
E_temp=El_ds(1)
N_temp=Nl_ds(1)
temp=0
20011 x=res/50.
temp=temp+x
E_temp=E_temp+x*(El_ds(2)-El_ds(1))/dist
N_temp=N_temp+x*(Nl_ds(2)-Nl_ds(1))/dist
!write(6,*)E_temp,N_temp,dist
if(temp>=dist)then
   !write(6,*)'fin qua tutto ok'
   go to 2002
endif
temp_x=int(E_temp)-ovest
temp_y=nord-int(N_temp)
pixel_temp_i=1+int(temp_y/res)
pixel_temp_j=1+int(temp_x/res)
!write(6,*) pixel_temp_i, pixel_temp_j
bordi_alveo(pixel_temp_i,pixel_temp_j)=1
go to 20011


!SINISTRA
2002 write (60,'(a6)')'L  2 1'
write (60,*)El_sx(1),Nl_sx(1)
write (60,*)El_sx(2),Nl_sx(2)
write (60,*)' 1     2'
dist=sqrt((El_sx(2)-El_sx(1))**2.+(Nl_sx(2)-Nl_sx(1))**2.)
E_temp=El_sx(1)
N_temp=Nl_sx(1)
temp=0
20021 x=res/50.
temp=temp+x
E_temp=E_temp+x*(El_sx(2)-El_sx(1))/dist
N_temp=N_temp+x*(Nl_sx(2)-Nl_sx(1))/dist
if(temp>=dist)then
   go to 1000
endif
temp_x=int(E_temp)-ovest
temp_y=nord-int(N_temp)
pixel_temp_i=1+int(temp_y/res)
pixel_temp_j=1+int(temp_x/res)
bordi_alveo(pixel_temp_i,pixel_temp_j)=1
go to 20021

1001 rewind(51)
rewind(53)


!ora mi memorizzo il profilo in un'array opportunamente creato
allocate(profilo(nrighe))
allocate(E(nrighe))
allocate(N(nrighe))


do i=1,nrighe
   profilo(i)=0
enddo


f=0
i=0
3000 i=i+1
if (i==nrighe) then
   go to 4000
endif
read(51,*)E1, N1, z
!write(6,*)i, E1, N1
!write(6,*)i, E1dopo, trim(tab), N1dopo
if (E1<ovest .or. E1>est .or. N1>nord .or. N1<sud) then
   go to 3000
else
   f=f+1
   E(f)=E1
   N(f)=N1
   profilo(f)=z
   go to 3000
endif


4000 nsez=f
write(6,*) "There are", nsez, "section"
rewind(51)


do ii=1,nbordi
   !write(6,*) ii, 'ok', nbordi
   read(53,*) Ebordo, Nbordo, quotal, temp1, h1
  ! write(6,*) Ebordo, Nbordo, quotal, temp1, h1
   if(h1/=1 .or. h1/=nsez) then
      EEE=E(h1)
      NNN=N(h1)
      zzz=profilo(h1)
      !write(6,*)ii, 'fin qua ok'
      call muoviti
   endif
enddo



write(6,*) 'End of computational step → WRITING OUTPUT'
!write(60,*)  ((bordi_alveo(i,j), j=1,colonne), i=1,righe)
write(61,*)  ((reticolo2d(i,j), j=1,colonne), i=1,righe)

write(6,*) 'END of Fortran Code → OK'
end program reticolo_2d_fuori_alveo











!****************************************************************************************************************************************
!SUBROUTINE DIREZIONE
!****************************************************************************************************************************************
subroutine muoviti
USE dati
USE dd
implicit none

real::EST1,EST2,NORD1,NORD2,LIVELLO
!real,intent(IN)::EST1
!real,intent(IN)::EST2
!real,intent(IN)::NORD1
!real,intent(IN)::NORD2
!real,intent(IN)::LIVELLO
integer::iii, i_temp, j_temp, iiii, jjjj
real::vettore_direzione, quota_min, temp, dist_temp, xxx, E_t, N_t, passo, xxxx
character(1)::dir
!(EEE,Ebordo,NNN,Nbordo,zzz)
!(EST1,EST2,NORD1,NORD2,LIVELLO)

EST1=EEE
NORD1=NNN
EST2=Ebordo
NORD2=Nbordo
LIVELLO=zzz

!****************************************************************************************************************************************
!SOLO IN ENTRATA
quota_min=0
i=1+int((nord-NORD2)/res)
j=1+int((EST2-ovest)/res)
vettore_direzione=((NORD2-NORD1)/(EST2-EST1))
!assegno dir positiva qualora y(i+1)>y(i) viceversa dir negativa
if(NORD2>=NORD1)then
   dir='+'
else
   dir='-'
endif
dist_temp=sqrt((NORD2-NORD1)**2+(EST2-EST1)**2)
iii=0
1111 xxx=res
temp=EST2+xxx*(EST2-EST1)/dist_temp
j=1+int((temp-ovest)/res)
temp=NORD2+xxx*(NORD2-NORD1)/dist_temp
i=1+int((nord-temp)/res)
!write(6,*)i, j, righe, colonne
if(i<1 .or. j<1 .or. i>righe .or. j>colonne) then
   write(6,*) '!!!ATTENTION i =', i, ' j = ', j, ' row = ', righe, &
 'col = ', colonne, 'Out of region'
   go to 10001
endif
reticolo2d(i,j)=LIVELLO
iii=iii+1
if(iii==1) then
   go to 1111
endif


!****************************************************************************************************************************************



!****************************************************************************************************************************************
!OGNI VOLTA
10000 if(vettore_direzione>-0.414 .and. vettore_direzione<0 .and. dir=='+') then
   go to 30001
else if (vettore_direzione<0.414 .and. vettore_direzione>=0 .and. dir=='-') then
   go to 30001
else if (vettore_direzione<-0.414 .and. vettore_direzione>=-2.414 .and. dir=='+') then
   go to 40001
else if (abs(vettore_direzione)>2.414 .and. dir=='+') then
   go to 50001
else if (vettore_direzione<=2.414 .and. vettore_direzione>0.414 .and. dir=='+') then
   go to 60001
else if (vettore_direzione<=0.414 .and. vettore_direzione>=0 .and. dir=='+') then
   go to 30002
else if (vettore_direzione>-0.414 .and. vettore_direzione<0 .and. dir=='-') then
   go to 30002
else if (vettore_direzione<=-0.414 .and. vettore_direzione>-2.414 .and. dir=='-') then
   go to 40002
else if (abs(vettore_direzione)>2.414 .and. dir=='-') then
   go to 50002
else if (vettore_direzione<=2.414 .and. vettore_direzione>0.414 .and. dir=='-') then
   go to 60002
else
   write(6,*) 'ATTENTION → problem in subroutine muoviti'
endif
!****************************************************************************************************************************************




!*****************************************************************************************************************************************
30001 vettore_direzione=4
if(reticolo2d(i,j-1)/=LIVELLO)then
   quota_min=quota_terreno(i,j-1)
   vettore_direzione=0
   dir='-'
else 
   quota_min=LIVELLO
endif
if(quota_terreno(i-1,j-1)<quota_min .and. reticolo2d(i-1,j-1)/=LIVELLO)then
   quota_min=quota_terreno(i-1,j-1)
   vettore_direzione=-1
   dir='+'
endif
if(quota_terreno(i+1,j-1)<quota_min .and. reticolo2d(i+1,j-1)/=LIVELLO)then
   quota_min=quota_terreno(i+1,j-1)
   vettore_direzione=1
   dir='-'
endif
if(quota_terreno(i-1,j)<quota_min .and. reticolo2d(i-1,j)/=LIVELLO)then
   quota_min=quota_terreno(i-1,j)
   vettore_direzione=3
   dir='+'
endif
if(quota_terreno(i+1,j)<quota_min .and. reticolo2d(i+1,j)/=LIVELLO)then
   quota_min=quota_terreno(i+1,j)
   vettore_direzione=3
   dir='-'
endif
go to 70000

!****************************************************************************************************************************************
30002 vettore_direzione=4
if(reticolo2d(i,j+1)/=LIVELLO)then
   quota_min=quota_terreno(i,j+1)
   vettore_direzione=0
   dir='+'
else 
   quota_min=LIVELLO
endif
if(quota_terreno(i-1,j+1)<quota_min .and. reticolo2d(i-1,j+1)/=LIVELLO)then
   quota_min=quota_terreno(i-1,j+1)
   vettore_direzione=1
   dir='+'
endif
if(quota_terreno(i+1,j+1)<quota_min .and. reticolo2d(i+1,j+1)/=LIVELLO)then
   quota_min=quota_terreno(i+1,j+1)
   vettore_direzione=-1
   dir='-'
endif
if(quota_terreno(i-1,j)<quota_min .and. reticolo2d(i-1,j)/=LIVELLO)then
   quota_min=quota_terreno(i-1,j)
   vettore_direzione=3
   dir='+'
endif
if(quota_terreno(i+1,j)<quota_min .and. reticolo2d(i+1,j)/=LIVELLO)then
   quota_min=quota_terreno(i+1,j)
   vettore_direzione=3
   dir='-'
endif

go to 70000


!****************************************************************************************************************************************
40001 vettore_direzione=4
if(reticolo2d(i-1,j-1)/=LIVELLO)then
   quota_min=quota_terreno(i-1,j-1)
   vettore_direzione=-1
   dir='+'
else 
   quota_min=LIVELLO
endif
if(quota_terreno(i-1,j)<quota_min .and. reticolo2d(i-1,j)/=LIVELLO)then
   quota_min=quota_terreno(i-1,j)
   vettore_direzione=3
   dir='+'
endif
if(quota_terreno(i,j-1)<quota_min .and. reticolo2d(i,j-1)/=LIVELLO)then
   quota_min=quota_terreno(i,j-1)
   vettore_direzione=0
   dir='-'
endif
if(quota_terreno(i-1,j+1)<quota_min .and. reticolo2d(i-1,j+1)/=LIVELLO)then
   quota_min=quota_terreno(i-1,j+1)
   vettore_direzione=1
   dir='+'
endif
if(quota_terreno(i+1,j-1)<quota_min .and. reticolo2d(i+1,j-1)/=LIVELLO)then
   quota_min=quota_terreno(i+1,j-1)
   vettore_direzione=1
   dir='-'
endif

go to 70000

!****************************************************************************************************************************************
40002  vettore_direzione=4
if(reticolo2d(i+1,j+1)/=LIVELLO)then
   quota_min=quota_terreno(i+1,j+1)
   vettore_direzione=-1
   dir='-'
else 
   quota_min=LIVELLO
endif
if(quota_terreno(i,j+1)<quota_min .and. reticolo2d(i,j+1)/=LIVELLO)then
   quota_min=quota_terreno(i,j+1)
   vettore_direzione=0
   dir='+'
endif
if(quota_terreno(i+1,j)<quota_min .and. reticolo2d(i+1,j)/=LIVELLO)then
   quota_min=quota_terreno(i+1,j)
   vettore_direzione=3
   dir='-'
endif
if(quota_terreno(i-1,j+1)<quota_min .and. reticolo2d(i-1,j+1)/=LIVELLO)then
   quota_min=quota_terreno(i-1,j+1)
   vettore_direzione=1
   dir='+'
endif
if(quota_terreno(i+1,j-1)<quota_min .and. reticolo2d(i+1,j-1)/=LIVELLO)then
   quota_min=quota_terreno(i+1,j-1)
   vettore_direzione=1
   dir='-'
endif
go to 70000

!****************************************************************************************************************************************
50001 vettore_direzione=4
if(reticolo2d(i-1,j)/=LIVELLO)then
   quota_min=quota_terreno(i-1,j)
   vettore_direzione=3
   dir='+'
else 
   quota_min=LIVELLO
endif
if(quota_terreno(i-1,j+1)<quota_min .and. reticolo2d(i-1,j+1)/=LIVELLO)then
   quota_min=quota_terreno(i-1,j+1)
   vettore_direzione=1
   dir='+'
endif
if(quota_terreno(i-1,j-1)<quota_min .and. reticolo2d(i-1,j-1)/=LIVELLO)then
   quota_min=quota_terreno(i-1,j-1)
   vettore_direzione=-1
   dir='+'
endif
if(quota_terreno(i,j+1)<quota_min .and. reticolo2d(i,j+1)/=LIVELLO)then
   quota_min=quota_terreno(i,j+1)
   vettore_direzione=0
   dir='+'
endif
if(quota_terreno(i,j-1)<quota_min .and. reticolo2d(i,j-1)/=LIVELLO)then
   quota_min=quota_terreno(i,j-1)
   vettore_direzione=0
   dir='-'
endif
go to 70000
!****************************************************************************************************************************************
50002  vettore_direzione=4
if(reticolo2d(i+1,j)/=LIVELLO)then
   quota_min=quota_terreno(i+1,j)
   vettore_direzione=3
   dir='-'
else 
   quota_min=LIVELLO
endif
if(quota_terreno(i+1,j+1)<quota_min .and. reticolo2d(i+1,j+1)/=LIVELLO)then
   quota_min=quota_terreno(i+1,j+1)
   vettore_direzione=-1
   dir='-'
endif
if(quota_terreno(i+1,j-1)<quota_min .and. reticolo2d(i+1,j-1)/=LIVELLO)then
   quota_min=quota_terreno(i+1,j-1)
   vettore_direzione=1
   dir='-'
endif
if(quota_terreno(i,j+1)<quota_min .and. reticolo2d(i,j+1)/=LIVELLO)then
   quota_min=quota_terreno(i,j+1)
   vettore_direzione=0
   dir='+'
endif
if(quota_terreno(i,j-1)<quota_min .and. reticolo2d(i,j-1)/=LIVELLO)then
   quota_min=quota_terreno(i,j-1)
   vettore_direzione=0
   dir='-'
endif
go to 70000   
!****************************************************************************************************************************************
60001  vettore_direzione=4
if(reticolo2d(i-1,j+1)/=LIVELLO)then
   quota_min=quota_terreno(i-1,j+1)
   vettore_direzione=1
   dir='+'
else 
   quota_min=LIVELLO
endif
if(quota_terreno(i,j+1)<quota_min .and. reticolo2d(i,j+1)/=LIVELLO)then
   quota_min=quota_terreno(i,j+1)
   vettore_direzione=0
   dir='+'
endif
if(quota_terreno(i-1,j)<quota_min .and. reticolo2d(i-1,j)/=LIVELLO)then
   quota_min=quota_terreno(i-1,j)
   vettore_direzione=3
   dir='+'
endif
if(quota_terreno(i+1,j+1)<quota_min .and. reticolo2d(i+1,j+1)/=LIVELLO)then
   quota_min=quota_terreno(i+1,j+1)
   vettore_direzione=-1
   dir='-'
endif
if(quota_terreno(i-1,j-1)<quota_min .and. reticolo2d(i-1,j-1)/=LIVELLO)then
   quota_min=quota_terreno(i-1,j-1)
   vettore_direzione=-1
   dir='+'
endif
go to 70000
!****************************************************************************************************************************************
60002  vettore_direzione=4
if(reticolo2d(i+1,j-1)/=LIVELLO)then
   quota_min=quota_terreno(i+1,j-1)
   vettore_direzione=1
   dir='-'
else 
   quota_min=LIVELLO
endif
if(quota_terreno(i+1,j)<quota_min .and. reticolo2d(i+1,j)/=LIVELLO)then
   quota_min=quota_terreno(i+1,j)
   vettore_direzione=3
   dir='-'
endif
if(quota_terreno(i,j-1)<quota_min .and. reticolo2d(i,j-1)/=LIVELLO)then
   quota_min=quota_terreno(i,j-1)
   vettore_direzione=0
   dir='-'
endif
if(quota_terreno(i+1,j+1)<quota_min .and. reticolo2d(i+1,j+1)/=LIVELLO)then
   quota_min=quota_terreno(i+1,j+1)
   vettore_direzione=-1
   dir='-'
endif
if(quota_terreno(i-1,j-1)<quota_min .and. reticolo2d(i-1,j-1)/=LIVELLO)then
   quota_min=quota_terreno(i-1,j-1)
   vettore_direzione=-1
   dir='+'
endif



70000 if (vettore_direzione==1) then
   if(dir=='+')then
      i=i-1
      j=j+1
   else if (dir=='-')then
      i=i+1
      j=j-1
   endif
else if (vettore_direzione==3) then
   if(dir=='+')then
      i=i-1
      j=j
   else if (dir=='-')then
      i=i+1
      j=j
   endif
else if (vettore_direzione==0) then
   if(dir=='+')then
      i=i
      j=j+1
   else if (dir=='-')then
      i=i
      j=j-1
   endif
else if (vettore_direzione==-1)  then
   if(dir=='+')then
      i=i-1
      j=j-1
   else if (dir=='-')then
      i=i+1
      j=j+1
   endif
endif
   




!****************************************************************************************************************************************
!CONTROLLI DI ROUTINE ----> se li supero torno a 100000
!                     ----> se non li supero ho finito di muovermi
 if (quota_terreno(i,j)>=LIVELLO) then
   reticolo2d(i,j)=0
   go to 10001
else if (i>=righe .or. j>=colonne)then
   reticolo2d(i,j)=0
   go to 10001
else if ( bordi_alveo(i,j)==1)then
   go to 10001
else if (reticolo2d(i,j)>LIVELLO)then
   go to 10001
else if (quota_terreno(i,j)==0) then
   reticolo2d(i,j)=0
   go to 10001
else if (i==1 .or. j==1 .or. i==righe .or. j==colonne)then
   reticolo2d(i,j)=LIVELLO
   go to 10001
else
!else if (inondazioneT(i,j)==0)then
   iiii=i
   jjjj=j
   !write(6,*)'controllo con il 2x2', vettore_direzione, dir
   go to 20000
!else
!   reticolo2d(i,j)=LIVELLO
!   go to 10000
endif


!ripercorro l'ultimo tratto con risoluzione del dtm 2x2 per controllare che l'acqua non abbia superato un argine
20000 passo=res2
if(vettore_direzione==1 .and. dir=='+') then
   i=i+1
   j=j-1
   E_t=ovest+res*j-res/2
   N_t=nord-(res*i-res/2)
   !write(6,*)est,  E_t, ovest, sud, N_t, nord 
   xxxx=0
   11  xxxx=xxxx+passo
   E_t=E_t+passo/sqrt(2.)
   N_t=N_t+passo/sqrt(2.)
   if(xxxx>(sqrt(2.)*res)) then
      i=i-1
      j=j+1
      reticolo2d(iiii,jjjj)=LIVELLO
      go to 10000
   endif
   i_temp=1+int((nord-N_t)/res2)
   j_temp=1+int((E_t-ovest)/res2)
   !write(6,*) i_temp, righe2, J_temp,colonne2, inondazioneT_2(i_temp,j_temp)
   call trova_elemento(i_temp,j_temp)
   if(output>livello)then
     ! write(6,*) '0'
      reticolo2d(iiii,jjjj)=0
      go to 10001
   else
      !write(6,*) '1'
      go to 11
   endif   
else if (vettore_direzione==0 .and. dir=='+'  ) then
   i=i
   j=j-1
   E_t=ovest+res*j-res/2
   N_t=nord-(res*i-res/2)
  ! write(6,*)est,  E_t, ovest, sud, N_t, nord 
   xxxx=0
   15  xxxx=xxxx+passo
   E_t=E_t+passo
   if(xxxx>(res)) then
       i=i
       j=j+1
       reticolo2d(iiii,jjjj)=LIVELLO
      go to 10000
   endif
   i_temp=1+int((nord-N_t)/res2)
   j_temp=1+int((E_t-ovest)/res2)
   call trova_elemento(i_temp,j_temp)
   if(output>LIVELLO)then
      !write(6,*) '0'
      reticolo2d(iiii,jjjj)=0
      go to 10001
   else 
      !write(6,*) '1'
      go to 15
   endif   
else if (vettore_direzione==-1 .and. dir=='-') then
   i=i-1
   j=j-1
   E_t=ovest+res*j-res/2
   N_t=nord-(res*i-res/2)
   xxxx=0
   12 xxxx=xxxx+passo
   E_t=E_t+passo/sqrt(2.)
   N_t=N_t-passo/sqrt(2.)
   if(xxxx>(sqrt(2.)*res)) then
      j=j+1
      i=i+1
      reticolo2d(iiii,jjjj)=LIVELLO
      go to 10000
   endif
   i_temp=1+int((nord-N_t)/res2)
   j_temp=1+int((E_t-ovest)/res2)
   call trova_elemento(i_temp,j_temp)
   if(output>LIVELLO)then
      reticolo2d(iiii,jjjj)=0
      go to 10001
   else 
      go to 12
   endif   
else if (vettore_direzione==3 .and. dir=='-') then
   i=i-1
   j=j
   E_t=ovest+res*j-res/2
   N_t=nord-(res*i-res/2)
   xxxx=0
   17 xxxx=xxxx+passo
   N_t=N_t-passo
   if(xxxx>res) then
      i=i+1
      j=j
      reticolo2d(iiii,jjjj)=LIVELLO
      go to 10000
   endif
   i_temp=1+int((nord-N_t)/res2)
   j_temp=1+int((E_t-ovest)/res2)
   call trova_elemento(i_temp,j_temp)
   if(output>LIVELLO)then
      reticolo2d(iiii,jjjj)=0
      go to 10001
   else 
      go to 17
   endif   
else if (vettore_direzione==1 .and. dir=='-') then
   i=i-1
   j=j+1
   E_t=ovest+res*j-res/2
   N_t=nord-(res*i-res/2)
   xxxx=0
   13 xxxx=xxxx+passo
   E_t=E_t-passo/sqrt(2.)
   N_t=N_t-passo/sqrt(2.)
   if(xxxx>(sqrt(2.)*res)) then
      i=i+1
      j=j-1
      reticolo2d(iiii,jjjj)=LIVELLO
      go to 10000
   endif
   i_temp=1+int((nord-N_t)/res2)
   j_temp=1+int((E_t-ovest)/res2)
   call trova_elemento(i_temp,j_temp)
   if(output>LIVELLO)then
      reticolo2d(iiii,jjjj)=0
      go to 10001
   else 
      go to 13
   endif   
else if (vettore_direzione==0 .and. dir=='-') then
   i=i
   j=j+1
   E_t=ovest+res*j-res/2
   N_t=nord-(res*i-res/2)
   xxxx=0
   16  xxxx=xxxx+passo
   E_t=E_t-passo
   if(xxxx>(res)) then
      i=i
      j=j-1
      reticolo2d(iiii,jjjj)=LIVELLO
      go to 10000
   endif
   i_temp=1+int((nord-N_t)/res2)
   j_temp=1+int((E_t-ovest)/res2)
   call trova_elemento(i_temp,j_temp)
   if(output>LIVELLO)then
      reticolo2d(iiii,jjjj)=0
      go to 10001
   else 
      go to 16
   endif   
else if (vettore_direzione==-1 .and. dir=='+') then
   i=i+1
   j=j+1
   E_t=ovest+res*j-res/2
   N_t=nord-(res*i-res/2)
   xxxx=0
   14 xxxx=xxxx+passo
   E_t=E_t-passo/sqrt(2.)
   N_t=N_t+passo/sqrt(2.)
   if(xxxx>(sqrt(2.)*res)) then
      i=i-1
      j=j-1
      reticolo2d(iiii,jjjj)=LIVELLO
      go to 10000
   endif
   i_temp=1+int((nord-N_t)/res2)
   j_temp=1+int((E_t-ovest)/res2)
   call trova_elemento(i_temp,j_temp)
   if(output>LIVELLO)then
      reticolo2d(iiii,jjjj)=0
      go to 10001
   else 
      go to 14
   endif   
else if (vettore_direzione==3 .and. dir=='+') then
   i=i+1
   j=j
   E_t=ovest+res*j-res/2
   N_t=nord-(res*i-res/2)
   xxxx=0
   18 xxxx=xxxx+passo
   N_t=N_t+passo
   if(xxxx>res) then
      i=i-1
      j=j
      reticolo2d(iiii,jjjj)=LIVELLO
      go to 10000
   endif
   i_temp=1+int((nord-N_t)/res2)
   j_temp=1+int((E_t-ovest)/res2)
   call trova_elemento(i_temp,j_temp)
   if(output>LIVELLO)then
      reticolo2d(iiii,jjjj)=0
      go to 10001
   else 
      go to 18
   endif   
endif

 
10001 temp=0

end subroutine  muoviti









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
write(6,*)'There are', n_no_null, 'no-null cells in the Digital Terrain Model'

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



