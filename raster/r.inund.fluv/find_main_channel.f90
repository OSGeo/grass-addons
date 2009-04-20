module dd
integer,parameter::ferma_bisezione=15
integer::n_no_null
real, allocatable, dimension(:)::val, iind, jind
real::output
end module dd



!*************************************************************************************************************************************
!il programma in questione cerca dei limiti ragionevoli a destra e sinistra dell'alveo fluviale in questione
!questi limiti sono quelli al di là  dei quali ragionevolmente posso pensare che l'acqua è esondata
!saranno poi i limiti al di là  dei quali andrà  a cercare il reticolo idrografico in base alla massima pendenza
!COME AGISCE IL PROGRAMMA?
!il programma noto il livello centennale ne calcola una porzione 30% (in maniera tale da escludere i difetti del dtm a fondo alveo)
!quindi sale per step di mezzo metro e calcola i punti a dx o sx in cui l'acqua si scontra con il terreno (alveo)
!si ferma al punto in cui a destra o a sinistra c'è  una differenza sostanziale con il punto dello step prima
!(paremetro da decidere = 1m, 2m) 
!tra i 2 passi cerco il punto del dtm con max  pendenza "negativa" (quello è ¨il mio limite alveo)
!INPUT
!limiti della regione
!matrice col DTM
!profilo centennale
!OUTPUT
!vettoriale con i limiti dell'alveo
!***************************************************************************************************************************************


program trova_alveo
use dd
implicit none

!****************************************************************************************************************************************
!real, parameter:: res=2, par=2, step=0.5
!il programma è  pensato per una risoluzione del file raster 2x2 se la risoluzione fosse diversa MODIFICARE  il parametro res
!i valore 'par' e 'step' sono i valori su cui si basa il programma, modificare con ATTENZIONE
!****************************************************************************************************************************************
real::res, par, step
real:: nord, sud, est, ovest
integer::i, ii, iend, righe, colonne, nrighe, pixel_i, pixel_j, j, center_i, center_j, f
integer::pixel_temp_i, pixel_temp_j, temp_x, temp_y
!real, allocatable, dimension(:,:):: quota_terreno
!character(2), allocatable, dimension(:,:):: limiti_alveo
real(kind=8)::x, E1, N1, E1dopo, N1dopo, z, livello, E2, N2, dir_ortog, dist
real(kind=8):: E_temp, N_temp,  coord_N, coord_E, quota, dist_temp, quota_max
real(kind=8):: dist_destra, dist_sinistra, verifica_dist, pendenza, pendenza_max
real(kind=8):: quota_limite, quota_centro
character(len=40)::xx, tab, tab1
real,dimension(2)::quota_temp
real, dimension(500):: E_ds, N_ds, E_sx, N_sx
integer,allocatable,dimension(:)::i_ds, j_ds, i_sx, j_sx
real,allocatable,dimension(:)::quota_ds, quota_sx, EE, NN
character(40)::nomefile4,nomefile1, nomefile2, nomefile3
open(unit=40, status='old', file='nomefile.txt')
read(40,*) nomefile1, nomefile2, nomefile3, nomefile4
close(40)

! lettura parametri impostati dall'utente
open(unit=41, status='old', file='parameter.txt')
read(41,*)res, par, step 
close(41)

!50=region2.txt
!nomefile2=dtm2x2 (vd dopo)
!51=quote_100
!61=limiti_alveo_vect
write(6,*)trim(nomefile1)
open(unit=50, status='old', file=nomefile1)
open(unit=51, status='old', file=nomefile4)
open(unit=61, file=nomefile3)



!leggo le dimensioni della regione utili per allocare le matrici in cui memorizzare carta di input e di output
do i=1,13
   read(50,*)xx
   if (xx=='north:') then
      backspace(50) 
      read(50,*)xx, nord
      !write(60,'(a6,i)') trim(xx), nord
   else if (xx=='south:') then
      backspace(50) 
      read(50,*)xx, sud
      !write(60,'(a6,i)')trim(xx), sud
   else if (xx=='east:') then
      backspace(50) 
      read(50,*)xx, est
      !write(60,'(a5,i)') trim(xx), est
  ! else if (xx=='nsres') then
  !    backspace(50)
  !    read(50,*)xx, res
   else if (xx=='west:') then
      backspace(50) 
      read(50,*)xx, ovest
      !write(60,'(a5,i)')trim(xx), ovest
   else if (xx=='rows:') then
      backspace(50)  
      read(50,*)xx, righe
      !write(60,'(a5,i)')trim(xx), righe
   else if (xx=='cols:') then
      backspace(50) 
      read(50,*)xx, colonne
      !write(60,'(a5,i)')trim(xx), colonne
   endif
enddo
write(6,*) nord, sud, est, ovest,res, righe, colonne
rewind(50)
close(50)

!allocate(quota_terreno(righe,colonne))
!allocate(limiti_alveo(righe,colonne))


!leggo il DTM
!read(52,*) ((quota_terreno(i,j), j=1,colonne), i=1,righe)
!write(6,*) 'letto il DTM'
!rewind(52)
!close(52)

call matrice_sparsa (nomefile2,righe,colonne)
write(6,*) 'Read the Digital Terrain Model with Compressed Sparse Row (CSR) algorithm'


!do j=1,colonne
!   do i=1,righe
!      limiti_alveo(i,j)='*'
!   enddo
!enddo



                  
!guardo quant'è lungo il file che contiene il profilo
do i=1,10000000
   read(51,*,iostat=iend)xx
   if(iend /= 0)exit
enddo
if(iend > 0)then
   write(6,*)'Errore di lettura :',iend
   stop
endif
nrighe=i-1
write(6,*) 'Read',nrighe,' rows in file of water surface'
rewind(51)


allocate(i_ds(nrighe))
allocate(j_ds(nrighe))
allocate(quota_ds(nrighe))
allocate(i_sx(nrighe))
allocate(j_sx(nrighe))
allocate(quota_sx(nrighe))
allocate(EE(nrighe))
allocate(NN(nrighe))



do i=1,nrighe
   i_ds(i)=0
   j_ds(i)=0
   quota_ds(i)=0
   i_sx(i)=0
   j_sx(i)=0
   quota_sx(i)=0
enddo

i=0
f=0

!CICLO
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
!write(6,*)i, E1, N1, z
!stop
dir_ortog=-(E1dopo-E1)/(N1dopo-N1)
if((N1dopo-N1)==0)then
   dir_ortog=-99E10
endif
!write(6,*) dir_ortog
!ora devo dire in quale pixel sono
temp_x=int(E1)-ovest
temp_y=nord-int(N1)
center_i=1+int(temp_y/res)
center_j=1+int(temp_x/res)
call  trova_elemento(center_i,center_j)
quota_centro=output
livello=z-quota_centro
!cerco un secondo punto per costruire la retta
E2=E1+10
N2=N1+dir_ortog*(E2-E1)
dist=sqrt((E2-E1)**2.+(N2-N1)**2.)
!mi muovo sulla retta prima a ds e poi a sx


!************************************************************************************************************************************************************
!MI MUOVO A DESTRA
j=0
!elimino il 30%
livello = 3./10.*livello
2000 j=j+1
livello=livello+step
quota=livello+quota_centro
!write(6,*)i, j, f, z, step, livello, quota, quota_terreno(center_i, center_j)
if (quota>z)then
   quota=z
endif
x=0
2001 x=x+res
coord_E=E1+x*(E2-E1)/dist
coord_N=N1+x*(N2-N1)/dist
temp_x=int(coord_E)-ovest
temp_y=nord-int(coord_N)
!ora devo dire in quale pixel sono
pixel_i=1+int(temp_y/res)
pixel_j=1+int(temp_x/res)
!write(6,*) pixel_i, pixel_j, center_i, center_j
if(pixel_i>righe .or. pixel_i<=0 .or. pixel_j<=0 .or. pixel_j>colonne)then
   write(6,*) 'In' , f, "section of these region there isn't right boundary" 
   go to 2002
endif
call  trova_elemento(pixel_i,pixel_j)
if(output>=quota)then
   E_ds(j)=1+int(coord_E/res)*res
   N_ds(j)=1+int(coord_N/res)*res
   !write(6,*)j, coord_E, E_ds(j), coord_N, N_ds(j)
   if(j>1) then
      dist_destra=sqrt((E_ds(j)-E_ds(j-1))**2.+(N_ds(j)-N_ds(j-1))**2)
      !write(6,*)i,j,f,'sto andando a destra', dist_destra
      !write(6,*) z, quota
      if (dist_destra>par)then
         !CERCO IL PUNTO IN CORRISPONDENZA DEL QUALE LA PENDENZA è MAX VERSO DESTRA   '\   il punto ' è quello che considero come 
         !limite d'alveo oltre il quale calcolare il reticolo idrografico
         !dovrò ancora verificare che tale pendenza sia effettivamente verso l'esterno alveo
         !in caso contrario proseguo nel DTM fino a trovare un punto di pendenza verso l'esterno
         E_temp=E_ds(j-1)
         N_temp=N_ds(j-1)
         pixel_temp_i=1+int((nord-N_temp)/res)
         pixel_temp_j=int((E_temp-ovest)/res)+1
         !write(6,*)pixel_temp_i, pixel_temp_j, righe, colonne, E_temp, N_temp
         call  trova_elemento(pixel_temp_i,pixel_temp_j)
         quota_temp(1)=output
         pendenza_max=100
         verifica_dist=0
20011    x=2
         E_temp=E_temp+x*(E2-E1)/dist
         N_temp=N_temp+x*(N2-N1)/dist
         temp_x=int(E_temp)-ovest
         temp_y=nord-int(N_temp)
         pixel_temp_i=1+int(temp_y/res)
         pixel_temp_j=1+int(temp_x/res)
         if (pixel_temp_i<1 .or. pixel_temp_j<1 .or. pixel_temp_i>righe .or. pixel_temp_j>colonne)then
            write(6,*) "In", f , "NO right boundary  ~ the region is too small"
            go to 2002
         endif
         call  trova_elemento(pixel_temp_i,pixel_temp_j)
         quota_temp(2)=output
         if(quota_temp(2)==0)then
            go to 20012
         endif
         pendenza=(quota_temp(2)-quota_temp(1))/x
         if (pendenza<pendenza_max) then
            i_ds(f)=pixel_temp_i
            j_ds(f)=pixel_temp_j
            EE(f)=E_temp
            NN(f)=N_temp
            quota_ds(f)=quota_temp(2)
            pendenza_max=pendenza
         endif
         quota_temp(1)=quota_temp(2)
         verifica_dist=verifica_dist+x
         if(verifica_dist<dist_destra)then
            go to 20011
      	 else
           if(pendenza_max<=0) then
             write(61,*) EE(f), NN(f), quota_ds(f), z, f
              go to 2002
           else
              go to 20011
           endif
        endif
     else
        if(quota==z)then
           write(6,*)  'In', f, "section NO right boundary ~ SEE THE PARAMETER" 
           go to 2002
        endif
        go to 2000
     endif
  else
     go to 2000
  endif
else
   go to 2001
endif


20012  if(pendenza_max<=0) then
   write(61,*) EE(f), NN(f), quota_ds(f), z, f
   go to 2002
else
   write(6,*) "In", f, "section the boundary of river is out of DTM"
   go to 2002
endif


  
   
!************************************************************************************************************************************************************
!MI MUOVO A SINISTRA 

2002 livello=z-quota_centro
j=0
!elimino il 30%
livello = 3/10*livello
2003 j=j+1
livello=livello+step
quota=livello+quota_centro
!write(6,*)i, j, f, z, step, livello, quota, quota_terreno(center_i, center_j)
!stop
if (quota>z)then
   quota=z
endif  
x=-2
2004 x=x-2
coord_E=E1+x*(E2-E1)/dist
coord_N=N1+x*(N2-N1)/dist
temp_x=int(coord_E)-ovest
temp_y=nord-int(coord_N)
!ora devo dire in quale pixel sono
pixel_i=1+int(temp_y/res)
pixel_j=1+int(temp_x/res)
!write(6,*) pixel_i, pixel_j, center_i, center_j
if(pixel_i>righe .or. pixel_i<=0 .or. pixel_j<=0 .or. pixel_j>colonne)then
   write(6,*)'In' , f, "section of these region there isn't left boundary" 
   go to 1000
endif
call  trova_elemento(pixel_i,pixel_j) 
if(output>=quota)then
   E_sx(j)=1+int(coord_E/res)*res
   N_sx(j)=1+int(coord_N/res)*res
   !write(6,*) coord_E, E_ds(j), coord_N, N_ds(j)
   if(j>1) then
      dist_sinistra=sqrt((E_sx(j)-E_sx(j-1))**2.+(N_sx(j)-N_sx(j-1))**2)
      !write(6,*) i,j,f, 'sto andando a sinistra',dist_sinistra
      !write(6,*) z, quota
      if (dist_sinistra>par)then
         !CERCO IL PUNTO IN CORRISPONDENZA DEL QUALE LA PENDENZA è MAX VERSO SINISTRA /'   il punto ' è quello che considero come 
         !limite d'alveo oltre il quale calcolare il reticolo idrografico
         !dovrò ancora verificare che tale pendenza sia effettivamente verso l'esterno alveo
         !in caso contrario proseguo nel DTM fino a trovare un punto di pendenza verso l'esterno
         E_temp=E_sx(j-1)
         N_temp=N_sx(j-1)
         pixel_temp_i=1+int((nord-N_temp)/res)
         pixel_temp_j=int((E_temp-ovest)/res)+1
         call  trova_elemento(pixel_temp_i,pixel_temp_j) 
         quota_temp(1)=output
         pendenza_max=100
         verifica_dist=0
20041    x=-res
         E_temp=E_temp+x*(E2-E1)/dist
         N_temp=N_temp+x*(N2-N1)/dist
         temp_x=int(E_temp)-ovest
         temp_y=nord-int(N_temp)
         pixel_temp_i=1+int(temp_y/res)
         pixel_temp_j=1+int(temp_x/res)
         if (pixel_temp_i<1 .or. pixel_temp_j<1 .or. pixel_temp_i>righe .or. pixel_temp_j>colonne)then
            write(6,*) "In", f , "NO left boundary  ~ the region is too small"
            go to 1000
         endif
         call  trova_elemento(pixel_temp_i,pixel_temp_j) 
         quota_temp(2)=output
         if(quota_temp(2)==0)then
            go to 20042
         endif
         pendenza=(quota_temp(2)-quota_temp(1))/x
         if (pendenza<pendenza_max) then
            i_sx(f)=pixel_temp_i
            j_sx(f)=pixel_temp_j
            EE(f)=E_temp
            NN(f)=N_temp
            quota_sx(f)=quota_temp(2)
            pendenza_max=pendenza
         endif
         quota_temp(1)=quota_temp(2)
         verifica_dist=verifica_dist+x
         if(abs(verifica_dist)<dist_destra)then
            go to 20041
      	 else
           if(pendenza_max<=0) then
              write(61,*) EE(f), NN(f), quota_sx(f), z, f
              go to 1000
           else
              go to 20041
           endif
      	endif
    else
       if(quota==z)then
          write(6,*)'In', f, "section NO left boundary ~ SEE THE PARAMETER" 
          go to 1000
       endif
       go to 2003
    endif
 else
    go to 2003
 endif
else
   go to 2004
endif

20042  if(pendenza_max<=0) then
   write(61,*) EE(f), NN(f), quota_sx(f), z, f
   go to 1000
else
   write(6,*)"In", f, "section the boundary of river is out of DTM"
   go to 1000
endif




1001 write(6,*) "End of water surface file"




write(6,*) 'Writing the boundary profile'

!write(60,*) ((limiti_alveo(i,j), j=1,colonne), i=1,righe)

deallocate(i_ds)
deallocate(j_ds)
deallocate(quota_ds)
deallocate(i_sx)
deallocate(j_sx)
deallocate(quota_sx)
deallocate(EE)
deallocate(NN)

write(6,*) 'END of Fortran Code ~ OK'
end program trova_alveo









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
write(6,*)'There are', n_no_null, 'no-null cells in Digital Terrain Model '

allocate (val(n_no_null))
allocate (jind(n_no_null))


cont=0
cont2=0
do i=1,righe
   cont2=cont+1
   iind(i)=cont2
   read (70,*) (temp(j),j=1,colonne)
   do j=1,colonne
      if (temp(j)/=0.)then 
         cont=cont+1	
         val(cont)=temp(j)
         jind(cont)=j	
      endif
   enddo
enddo
iind(righe+1)=n_no_null+1

rewind(70)
close(70)

!write(6,*) "val=", val
!write(6,*) "iind=", iind
!write(6,*) "jind=", jind
!stop

end subroutine matrice_sparsa





!************************************************************************************************
!Subroutine trova punto in matrice sparsa
!************************************************************************************************

subroutine trova_elemento(iriga,jcolonna)
use dd
implicit none
integer::i,iriga,jcolonna, iniz, fine

if (iind(iriga)==iind(iriga+1))then
   output=0.
   go to 144
endif
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
!write(6,*) output,iriga, jcolonna, iniz, fine

end subroutine trova_elemento
