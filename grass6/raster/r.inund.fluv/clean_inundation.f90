module dd
integer,parameter::ferma_bisezione=15
integer::n_no_null
real, allocatable, dimension(:)::val, iind, jind
real::output
end module dd



!*********************************************************************************************************************************
!il programma si muove su ogni pixel della carta raster di inondazione che è già stata pulita dai "laghi", 
!dove il pixel vale 0 (NON inondato) lasci stare tutto com'è
!dove il pixel vale 1 (inondato)-->  cerca il punto del profilo più vicino,
!                                    calcola la retta che unisce il pixel al profilo
!                                    si muove su questa retta e controlla se i pixel attraversati sono asciutti o bagnati
!                                         se asciutti--> il pixel diventa anch'esso asciutto
!                                         se bagnati il pixel rimane bagnato
!*********************************************************************************************************************************

program pulizia
use dd
implicit none
real::est, ovest, nord, sud, nord1, sud1, est1, ovest1
integer::i, j, ii, righe, colonne, iend, nrighe, int_x, int_y, row, col
integer::pixel_i, pixel_j, temp_x, temp_y, righe1, colonne1 
integer, allocatable, dimension(:,:):: inond_nuova, inond
real(kind=8)::passo, ver, coord_est, coord_nord, x, y, dist, dist_temp, E1, N1,res, res1
real, allocatable,dimension(:)::E, N, q
character(len=20)::xx, xx1
real, allocatable, dimension(:,:)::quota
character(40)::nomefile1, nomefile2, nomefile3, nomefile4
character(40)::nomefile5, nomefile6, nomefile7
open(unit=40, status='old', file='nomefile.txt')
read(40,*)nomefile1, nomefile2, nomefile3, nomefile4, nomefile5, nomefile6, nomefile7
close(40)



!apertura file   
!********************************************************************************************************************************
!N.B. controlla il nome file 
!********************************************************************************************************************************
!50=region20
!51=quote_punti_adiacenti (superficie idrica ottenuta con interpolazone lineare)
!52=inondazione_step2
!53=file con il profilo
!54=region2
!dtm2x2= nomefile7 (vd dopo)
!60=inondazione_nuova (step3)

open (unit=50, status='old', file=nomefile5)
open (unit=51, status='old', file=nomefile4)
open (unit=52, status='old', file=nomefile1)
open (unit=53, status='old', file=nomefile2)
open (unit=54, status='old', file=nomefile6)
!open (unit=55, status='old', file='grass_script/dtm2x2')
open (unit=60, file=nomefile3)



!guardo quant'è lungo il file che contiene il profilo
do i=1,10000000
   read(53,*,iostat=iend)xx
   if(iend /= 0)exit
enddo
if(iend > 0)then
   write(6,*)'Error reading file of water surface pofile:',iend
   stop
endif
nrighe=i-1
write(6,*) 'The file of water surface profile has ',nrighe,' rows'
rewind(53)

allocate(E(nrighe))
allocate(N(nrighe))
allocate(q(nrighe))

do i=1,nrighe
   read(53,*) E(i), N(i), q(i)
enddo

!leggo le dimensioni della regione meno dettagliata
do i=1,13
   read(50,*)xx
   if (xx=='north:') then
      backspace(50) 
      read(50,*)xx, nord
     ! write(60,'(a6,i)') trim(xx), nord
      write(60,'(a6,f10.2)') trim(xx), nord
      !write(60,*) trim(xx), nord
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
   else if (xx=='nsres:') then
      backspace(50) 
      read(50,*)xx, res
   endif
enddo
write(6,*) nord, sud, est, ovest, righe, colonne
close(50)




!alloco le matrici del file
allocate(quota(righe,colonne))
allocate(inond_nuova(righe,colonne))
allocate(inond(righe,colonne))

read(51,*) ((quota(i,j), j=1,colonne), i=1,righe)
write(6,*) 'Read the raster map with water surface'
read(52,*) ((inond(i,j), j=1,colonne), i=1,righe)
write(6,*) 'Read the raster inondation map of step 1'
close(51)
close(52)

!leggo le dimensioni della regione con risoluzione dettagliata
do i=1,13
   read(54,*)xx
   if (xx=='north:') then
      backspace(54) 
      read(54,*)xx, nord1
   else if (xx=='south:') then
      backspace(54) 
      read(54,*)xx, sud1
   else if (xx=='east:') then
      backspace(54) 
      read(54,*)xx, est1
   else if (xx=='west:') then
      backspace(54) 
      read(54,*)xx, ovest1
   else if (xx=='rows:') then
      backspace(54)  
      read(54,*)xx, righe1
   else if (xx=='cols:') then
      backspace(54) 
      read(54,*)xx, colonne1
   else if (xx=='nsres:') then
      backspace(54) 
      read(54,*)xx, res1
   endif
enddo
write(6,*) nord1, sud1, est1, ovest1, righe1, colonne1, res1


!open(unit=70,file='control.txt')
!write(70,*)res1
!close(70)
!allocate(quota_terreno(righe1,colonne1))

!leggo il DTM
!read(55,*) ((quota_terreno(i,j), j=1,colonne1), i=1,righe1)
!write(6,*) 'letto il DTM'
!rewind(55)
!close(55)

call matrice_sparsa (nomefile7,righe1,colonne1)
write(6,*) 'Read the Digital Terrain Model with Compressed Sparse Row Algorithm'

!scorro tutti i pixel della matrice inondazione 
!se trovo 0 (area NON inondata) ricopio il valore nella nuova matrice
!se trovo 1 eseguo il controllo e vedo se lasciare 1 o 0

j=0
i=0
1000 j=j+1
1001 i=i+1
!write(6,*)i,j
if(i==righe+1) then
   if(j==colonne)then
      go to 3000
   endif
   i=0
   go to 1000
endif

if(inond(i,j)==0) then
   inond_nuova(i,j)=inond(i,j)
   go to 1001
else if(inond(i,j)==1) then
   coord_est=ovest+res*j-res/2
   coord_nord=nord-(res*i-res/2)
   !write(6,*) coord_est,coord_nord,i,j
   !cerco il punto del profilo più vicino al mio pixel 
   dist=100000
   do ii=1,nrighe
      if (q(ii)==quota(i,j)) then
         dist_temp=sqrt((coord_est-E(ii))**2+(coord_nord-N(ii))**2)
         if(dist_temp<=dist) then
            E1=E(ii)
            N1=N(ii)
            dist=dist_temp
         endif
      endif
   enddo
   !controllo  
   if(E1>est .or. E1<ovest .or. N1>nord .or. N1<sud) then
      write(6, *) 'A point of water surface profile is out of region Est=',E1, 'Nord=',N1
      if(E1>est)then
         E1=est
         dist=sqrt((coord_est-E1)**2+(coord_nord-N1)**2)
      else if (E1<ovest) then 
         E1=ovest
         dist=sqrt((coord_est-E1)**2+(coord_nord-N1)**2)
      else if (N1>nord) then
         N1=nord
         dist=sqrt((coord_est-E1)**2+(coord_nord-N1)**2)
      else if (N1<sud) then
         N1=sud 
         dist=sqrt((coord_est-E1)**2+(coord_nord-N1)**2)
      endif
   endif
   rewind(53)

   !mi muovo sulla retta che congiunge l'alveo al pixel con un passo pari alla risoluzione più dettagliata
   passo=res1
   ver=0.
   x=coord_est
   y=coord_nord
   7000 ver=ver+passo
   x=x+passo*(E1-coord_est)/dist
   y=y+passo*(N1-coord_nord)/dist
   !ora devo dire in quale pixel sono
   pixel_i=1+int((nord1-y)/res1)
   pixel_j=1+int((x-ovest1)/res1)
   if (ver>dist) then
      inond_nuova(i,j)=inond(i,j)
      go to 1001
   endif
   call trova_elemento(pixel_i,pixel_j)
   if (output>quota(i,j))then
      inond_nuova(i,j)=0
      go to 1001
   else
      go to 7000
   endif
endif



!scrivo la nuova matrice
3000 write(6,*) 'Writing output raster Map'
222 format(5000(i1,1x))
write(60,222) ((inond_nuova(i,j), j=1,colonne),i=1,righe)
!write(60,'(i1)') ((inond_nuova(i,j), j=1,colonne),i=1,righe)
!write(61,'(b)') ((inond_nuova(i,j), j=1,colonne),i=1,righe)
    

deallocate(E)
deallocate(N)
deallocate(q)
deallocate(quota)
deallocate(inond_nuova)
deallocate(inond)


write(6,*)"END of Fortran code → OK"
end program pulizia









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

write(6,*)'There are', n_no_null, 'no null cells in Digital Terrain Model'
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
    
