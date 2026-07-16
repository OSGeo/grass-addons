! test_6sv_compat.f90 — calls 6SV2.1 subroutines with known inputs and
! prints key=value pairs consumed by testsuite/test_fortran_compat.py.
!
! Compile (linking 6SV2.1 .o objects built with 'make sixs' in ~/dev/6sV2.1/):
!   gfortran -O test_6sv_compat.f90 \
!       ~/dev/6sV2.1/CHAND.o ~/dev/6sV2.1/ODRAYL.o ~/dev/6sV2.1/VARSOL.o \
!       ~/dev/6sV2.1/SOLIRR.o ~/dev/6sV2.1/CSALBR.o ~/dev/6sV2.1/GAUSS.o \
!       ~/dev/6sV2.1/US62.o -lm -o test_6sv_compat
!
! Run:
!   ./test_6sv_compat

program test_6sv_compat
  implicit none

  ! COMMON blocks shared with the 6SV2.1 subroutines
  real :: delta, sigma
  common /sixs_del/ delta, sigma

  integer :: iwr
  logical :: ier
  common /sixs_ier/ iwr, ier

  ! Working variables
  real    :: xphi, xmuv, xmus, xtau, xrray
  real    :: wl, tray, swl, xalb, dsol
  real    :: x(48), w(48)
  integer :: n, jday, month, i

  ! Initialise COMMON blocks
  delta = 0.0279
  sigma = 0.0
  iwr   = 6        ! stdout
  ier   = .false.

  ! Initialise US62 standard atmosphere (fills /sixs_atm/ COMMON)
  call us62

  ! ── CHAND ────────────────────────────────────────────────────────────────────
  ! Test 1: backscatter geometry, moderate tau
  xphi = 0.0 ; xmuv = 0.9 ; xmus = 0.8 ; xtau = 0.1
  call chand(xphi, xmuv, xmus, xtau, xrray)
  write(*,'(A,F20.12)') 'chand_1=', xrray

  ! Test 2: 90° azimuth, moderate tau
  xphi = 90.0 ; xmuv = 0.7 ; xmus = 0.6 ; xtau = 0.2
  call chand(xphi, xmuv, xmus, xtau, xrray)
  write(*,'(A,F20.12)') 'chand_2=', xrray

  ! Test 3: forward scatter (phi=180), equal angles
  xphi = 180.0 ; xmuv = 0.5 ; xmus = 0.5 ; xtau = 0.3
  call chand(xphi, xmuv, xmus, xtau, xrray)
  write(*,'(A,F20.12)') 'chand_3=', xrray

  ! Test 4: 45° azimuth, small tau
  xphi = 45.0 ; xmuv = 0.8 ; xmus = 0.7 ; xtau = 0.05
  call chand(xphi, xmuv, xmus, xtau, xrray)
  write(*,'(A,F20.12)') 'chand_4=', xrray

  ! ── ODRAYL ───────────────────────────────────────────────────────────────────
  ! Rayleigh optical depth at visible/NIR wavelengths
  wl = 0.45 ; call odrayl(wl, tray) ; write(*,'(A,F20.12)') 'odrayl_045=', tray
  wl = 0.55 ; call odrayl(wl, tray) ; write(*,'(A,F20.12)') 'odrayl_055=', tray
  wl = 0.65 ; call odrayl(wl, tray) ; write(*,'(A,F20.12)') 'odrayl_065=', tray
  wl = 0.87 ; call odrayl(wl, tray) ; write(*,'(A,F20.12)') 'odrayl_087=', tray

  ! ── VARSOL ───────────────────────────────────────────────────────────────────
  ! dsol = 1/d²; jday is day-in-month, month 1-12
  jday = 3  ; month = 1  ! DOY   3 (perihelion)
  call varsol(jday, month, dsol)
  write(*,'(A,F20.12)') 'varsol_doy003=', dsol

  jday = 31 ; month = 3  ! DOY  90 (vernal equinox)
  call varsol(jday, month, dsol)
  write(*,'(A,F20.12)') 'varsol_doy090=', dsol

  jday = 4  ; month = 7  ! DOY 185 (aphelion)
  call varsol(jday, month, dsol)
  write(*,'(A,F20.12)') 'varsol_doy185=', dsol

  jday = 27 ; month = 9  ! DOY 270 (autumnal equinox)
  call varsol(jday, month, dsol)
  write(*,'(A,F20.12)') 'varsol_doy270=', dsol

  ! ── SOLIRR ───────────────────────────────────────────────────────────────────
  ! On-grid wavelengths (exact multiples of 0.0025 µm from 0.25 µm)
  ! → nearest-neighbour and linear interpolation give identical results here
  wl = 0.45 ; call solirr(wl, swl) ; write(*,'(A,F20.10)') 'solirr_045=', swl
  wl = 0.55 ; call solirr(wl, swl) ; write(*,'(A,F20.10)') 'solirr_055=', swl
  wl = 0.65 ; call solirr(wl, swl) ; write(*,'(A,F20.10)') 'solirr_065=', swl
  wl = 0.87 ; call solirr(wl, swl) ; write(*,'(A,F20.10)') 'solirr_087=', swl

  ! Off-grid wavelength: Fortran uses nearest-neighbour, C uses linear.
  ! The two values should agree to within 0.2% (solar spectrum is smooth here).
  wl = 0.5512 ; call solirr(wl, swl) ; write(*,'(A,F20.10)') 'solirr_05512=', swl

  ! ── CSALBR ───────────────────────────────────────────────────────────────────
  xtau = 0.1 ; call csalbr(xtau, xalb) ; write(*,'(A,F20.12)') 'csalbr_01=', xalb
  xtau = 0.3 ; call csalbr(xtau, xalb) ; write(*,'(A,F20.12)') 'csalbr_03=', xalb
  xtau = 0.5 ; call csalbr(xtau, xalb) ; write(*,'(A,F20.12)') 'csalbr_05=', xalb

  ! ── GAUSS ────────────────────────────────────────────────────────────────────
  ! 4-point Gauss-Legendre quadrature on [-1, 1]
  n = 4
  call gauss(-1.0, 1.0, x, w, n)
  do i = 1, n
    write(*,'(A,I1,A,F22.15)') 'gauss_x4_', i, '=', x(i)
    write(*,'(A,I1,A,F22.15)') 'gauss_w4_', i, '=', w(i)
  end do

  ! 8-point Gauss-Legendre quadrature on [-1, 1]
  n = 8
  call gauss(-1.0, 1.0, x, w, n)
  do i = 1, n
    write(*,'(A,I1,A,F22.15)') 'gauss_x8_', i, '=', x(i)
    write(*,'(A,I1,A,F22.15)') 'gauss_w8_', i, '=', w(i)
  end do

  stop
end program test_6sv_compat
