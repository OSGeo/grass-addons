# -*- coding: utf-8 -*-

#######################################################################
### Reference Knowledgebase with Demos for the SPEARFISH location
#######################################################################

def knowledgebase():
    #this function returns a huge here document, which is ingested by CLIPS instead or in addition to an external rulebase.
    # the string contains a rulebase containing demo rule-based actions in GRASS.


    payload="""
	;(assert (attract mode))
;attract mode sollte ein "fallback fact" werden, damit der user die KB wiederholt starten kann

(defrule isspearfish (declare (salience 101)) (LOCATION_NAME spearfish60) => 
  ;(ginfer_printout t "[Rule#1: Spearfish Location is confirmed]" crlf)
  (assert (attract mode)))


(defrule nospearfish (declare (salience 101)) (not (LOCATION_NAME spearfish60)) => (ginfer_printout t "PLEASE RESTART IN SPEARFISH LOCATION." crlf))

(defrule welcome (declare (salience 100)) (attract mode)  (LOCATION_NAME spearfish60) => 
 (ginfer_printout t " " crlf)
 (ginfer_printout t "******************************************************" crlf)
 (ginfer_printout t "*** Welcome to the g.infer Spearfish knowledgebase ***  " crlf)
 (ginfer_printout t "******************************************************" crlf)
 (ginfer_printout t " " crlf)
 (ginfer_printout t " " crlf)
 (ginfer_printout t "Available Demonstrations:" crlf)
 (ginfer_printout t " " crlf)
 (ginfer_printout t "[1]  Overview g.infer extensions to CLIPS" crlf)


 ; something with a loop on RHS
 ; something with variables on LHS
 ; something with variables on RHS
 ; mwas auf einem monitor darstellen
 ; dummy template benutzen, dafuer regeln aufstezen, spater ein raster einlesen, auf das dummy template umkopieren, regeln feuern
 (ginfer_printout t "[2] + GRASS: module call-up demo" crlf)
 (ginfer_printout t "[3] partial GRASS: WMS for on-demand raster import / Monitor demo" crlf)

 (ginfer_printout t "[4] + CLIPS: CLI-based user input demo" crlf)
 (ginfer_printout t "[5] NO CLIPS time-enabled rules demo" crlf)
 (ginfer_printout t "[6] + GRASS: Raster processing demo" crlf)
 (ginfer_printout t "[7] + GRASS: Vector processing demo" crlf)
 (ginfer_printout t "[8]- GRASS location/region manipulation demo" crlf)
 (ginfer_printout t "[a] tbd CLIPS: Facts manipulation (create / modify / remove) "  crlf)
 (ginfer_printout t "[b] tbd CLIPS: LHS Variables / Pattern Matching"  crlf)
 (ginfer_printout t "[c] tbd CLIPS: RHS Variables"  crlf)
 (ginfer_printout t "[d] tbd CLIPS: RHS sided loops/if then else"  crlf)
 (ginfer_printout t "[c] tbd CLIPS: Salience"  crlf)
 (ginfer_printout t "[e] tbd GRASS: Import a given Raster Layer during Inference runtime"  crlf)
 (ginfer_printout t "[e] tbd GRASS: Change all values of a raster layer like r.mapcal-style"  crlf)

(ginfer_printout t " " crlf)
 (ginfer_printout t "Please select a demo by entering its number/letter:" crlf)
 (ginfer_printout t " " crlf)
 (ginfer_printout t "Hint: this knowledgebase can be written to file using (save FILENAME) from the CLIPS prompt." crlf)

 (assert (demo_selection (ginfer_read t)))
 (assert (demo_selection_completed))
)

(defrule welcome_selection_01 (demo_selection_completed) (demo_selection 1) => 
 (ginfer_printout t "Selection= g.infer extensions overview" crlf)(assert (g.infer commands)))
 
(defrule welcome_selection_02 (demo_selection_completed) (demo_selection 2) => 
 (ginfer_printout t "Selection= GRASS modules demo" crlf)(assert (grassmodules demo)))

(defrule welcome_selection_03 (demo_selection_completed) (demo_selection 3) => 
 (ginfer_printout t "Selection= Raster WMS demo" crlf)(assert (raster_wms demo)))

(defrule welcome_selection_04 (demo_selection_completed) (demo_selection 4) => 
  (ginfer_printout t "Selection= CLIPS: User input / printout demo" crlf)(assert (readline demo)))

(defrule welcome_selection_05 (demo_selection_completed) (demo_selection 5) => 
  (ginfer_printout t "Selection= CLIPS time-enabled rules demo" crlf)(assert (time demo)))

(defrule welcome_selection_06 (demo_selection_completed) (demo_selection 6) => 
  (ginfer_printout t "Selection= Raster processing demo" crlf)(assert (raster demo)))

(defrule welcome_selection_07 (demo_selection_completed) (demo_selection 7) => 
  (ginfer_printout t "Selection= Vector processing demo" crlf)(assert (vector demo)))

(defrule welcome_selection_08 (demo_selection_completed) (demo_selection 8) => 
  (ginfer_printout t "Selection= GRASS location/region demo" crlf)(assert (region demo)))

(defrule welcome_selection_09 (demo_selection_completed) (demo_selection 9) => 
  (ginfer_printout t "Selection= bootstrap loader demo" crlf)(assert (bootstrap demo)))

;(defrule welcome_selection_A (demo_selection_completed) (demo_selection A) => (ginfer_printout t "Selection= Cellular automata demo" crlf)(assert (ca demo)))
;(defrule welcome_selection_B (demo_selection_completed) (demo_selection B) => (ginfer_printout t "Selection= R.mapcalc analogue demo" crlf)(assert (rmapcalc_rules demo)))

(defrule welcome_selection_09a (demo_selection_completed) (demo_selection a) => 
  (ginfer_printout t "Selection= CLIPS Facts manipulation demo" crlf)(assert (facts_101 demo)))

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; G.INFER EXTENSION COMMANDS [WORKS]:

(defrule extensions_001 (g.infer commands)  => 
 (ginfer_printout t "=============================================================== " crlf)
 (ginfer_printout t " " crlf)
 (ginfer_printout t "Special g.infer commands for the CLIPS command line interface: " crlf)
 (ginfer_printout t "" crlf)
 (ginfer_printout t " ==>   Invoke the commands by (python-call YOURCOMMAND) <== " crlf)
 (ginfer_printout t " " crlf)
 (ginfer_printout t "*** GENERAL: ***" crlf)
 (ginfer_printout t "* grass_run_command  " crlf)
 (ginfer_printout t "* grass_read_command  " crlf)
 (ginfer_printout t "* grass_start_command  " crlf)
 (ginfer_printout t "* ginfer_printout: CLIPS printout analog" crlf)
 (ginfer_printout t "* grass_message: Print a text message on the GRASS prompt" crlf)
 (ginfer_printout t "* grass_fatal: Print a warning message on the GRASS prompt and exit GRASS" crlf)
(ginfer_printout t "" crlf)
(ginfer_printout t "***  REGION / VARIABLES: ***" crlf)
(ginfer_printout t "* assert_region  " crlf)
(ginfer_printout t "* assert_gisenv  " crlf)
(ginfer_printout t "* grass.mapcalc  " crlf)
(ginfer_printout t "" crlf)
(ginfer_printout t "*** VECTOR: ***" crlf)
(ginfer_printout t "* assert_vector_metadata: Create fatcs from the metadata of a GRASS vector layer" crlf)
(ginfer_printout t "* grassvector2factlayer: Import a GRASS vector layer as facts  " crlf)
(ginfer_printout t "* grassvector2factlayer_internal  " crlf)
(ginfer_printout t "" crlf)
(ginfer_printout t "*** RASTER: ***" crlf)
(ginfer_printout t "* grass_raster_info  " crlf)
(ginfer_printout t "* grassraster2factlayer " crlf)
(ginfer_printout t "* grassraster2factlayer_internal  " crlf)
(ginfer_printout t "* grassvolume2factlayer  " crlf)
(ginfer_printout t "* grassvolume2factlayer_internal  " crlf)
(ginfer_printout t "" crlf)
(ginfer_printout t "*** OTHER: ***" crlf)
(ginfer_printout t "* pyprintout " crlf)
(ginfer_printout t "* pyreadline  " crlf)
(ginfer_printout t "* pyread  " crlf)
(ginfer_printout t "* pyclips_load " crlf)
(ginfer_printout t "^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^  " crlf)
)


;;;AUSSTEHEND:
; #clips.RegisterPythonFunction(factslayer_fromraster2grassraster_internal)
; #clips.RegisterPythonFunction(factslayer_fromraster3d2grassraster3d_internal)
; #clips.RegisterPythonFunction(factslayer2grassvector_internal)
; # Diese Funktionen erfordern das zentrale Speichern der EINGANGSINFORMATIONEN !
; #clips.RegisterPythonFunction(grass.raster_info)
; #clips.RegisterPythonFunction(LOADFACTS)
; #clips.RegisterPythonFunction(ASSERT_RASTER_METADATA)
; #clips.RegisterPythonFunction(DATENBANKZEUGS)
; #clips.RegisterPythonFunction(MAPCALC)
; #clips.RegisterPythonFunction("GRASS_LAMBDA")


;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;GRASS RUN [WORKS]:
(defrule grasscommandsdemo01 (grassmodules demo) => 
; a very simple LHS triggers the lengthy RHS
(python-call grass_message " ") 
; note that other print functions like ginfer_printout (the ginfer wrapper for CLIPS printout) could also be used. grass_message is a g.infer wrapper for the GRASS g.message module 
(python-call grass_message " ") 
(python-call grass_message "==========================================================================") 
 (python-call grass_message "-GRASS Modules Demo ")
 (python-call grass_message "=> using the grass_run_command extension of g.infer to start GRASS modules") 
 (python-call grass_message "------------------------------------------------------------------") 
 (python-call grass_message "   Invoking: g.version -g -b") 
 (python-call grass_message " ") 
 (python-call grass_run_command "g.version" "gb" )
 ;Note how the flags for g.version are provided without the leading "minus": Proper call on the GRASS shell would be "g.version -gb" or "g.version -g -b" 
 (python-call grass_message "---------------------------") 
 (python-call grass_message "   Invoking: g.region -pu") 
 (python-call grass_message " ") 
 (python-call grass_run_command "g.region" "pu" )
 (python-call grass_message "---------------------------") 
 (python-call grass_message "   Invoking g.list -f type=vect") 
 (python-call grass_message " ")
 (python-call grass_run_command "g.list" "f" "type=vect")
 ;(python-call grass_message "---------------------------") 
 (python-call grass_message " ")
 (python-call grass_message "==========================================================================") 
(python-call grass_message " ") 
)



;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;READLINE [WORKS]
(defrule readline_test1 (readline demo) => 

 (ginfer_printout t  " " crlf) 
 (ginfer_printout t "==========================================================================" crlf) 
 (ginfer_printout t "- CLIPS: User input / printout demo " crlf)
 (ginfer_printout t "  Using ginfer_printout and ginfer_read g.infer extensions of the CLIPS commands printout and read" clrf)
 (ginfer_printout t  " " crlf) 
 (ginfer_printout  t "Type in some feedback, please:" crlf)
 (assert (userfeedback (ginfer_read t)))
 (ginfer_printout t "Thank you for your feedback." crlf)
 ; TBD: Printout the feedback
)

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;RASTER WMS Import [WORKS]

;; import
;; -- file r.in.gdal
; r.in.wms output=akl_srtm mapserver="http://onearth.jpl.nasa.gov/wms.cgi" -c layers=worldwind_dem format=geotiff style=short_int maxcols=100 maxrows=100

(defrule grassrun_rinwms (raster_wms demo) => 
 ;(python-call grass_message "** RHS: r.in.wms **")
 (ginfer_printout t  " " crlf) 
 (ginfer_printout t "==========================================================================" crlf) 
 (ginfer_printout t "- GRASS: Using a WMS to obtain a raster layer and a GRASS monitor to display it." crlf)
  (ginfer_printout t "*** Online Access Mandatory ! ***" crlf)
 (ginfer_printout t "  This uses r.in.wms, g.remove, g.rename, d.mon and d.rast on the RHS of multiple chained rules" clrf)
 (ginfer_printout t  " " crlf) 
 (ginfer_printout t  " 1) g.region region=landuse" crlf)
 (python-call grass_run_command g.region rast=landuse)
 (ginfer_printout t  " 2) r.in.wms -c -oo output=akl_srtm mapserver=http://onearth.jpl.nasa.gov/wms.cgi  layers=worldwind_dem format=geotiff style=short_int maxcols=100 maxrows=100" crlf) 
 (python-call grass_run_command r.in.wms "c" "-o" output=akl_srtm mapserver=http://onearth.jpl.nasa.gov/wms.cgi  layers=worldwind_dem format=geotiff style=short_int maxcols=100 maxrows=100) 
 (assert (rinwms done))
 )

(defrule grassrun_rinwms_remove (rinwms done) =>
   (python-call grass_message "  3) r.in.wms remove raster2 **") 
   (python-call grass_run_command g.remove rast=akl_srtm.2) 
   (assert (rinwms_remove done)))

(defrule grassrun_rinwms_rename (rinwms_remove done) => 
   (python-call grass_message " 4) r.in.wms rename raster1 **") 
   (python-call grass_run_command g.rename rast=akl_srtm.1,rhs_srtm) 
   (ginfer_printout t " 5) Enter something to proceed:" crlf) 
   (assert (feedback (ginfer_read t))) 
   (assert (rinwms_rename done))
 )

(defrule grassrun_rinwms_display2 (rinwms_rename done) => 
    (python-call grass_message " 5) r.in.wms display **") 
    (python-call grass_run_command d.mon start=x0) 
    (python-call grass_run_command d.rast map=rhs_srtm) 
    (assert (rinwms_display1 done))
 )

(defrule grassrun_rinwms_display1 (rinwms_display1 done) => 
 (ginfer_printout t "Demo: Feedback, please:" crlf) 
 (assert (ducky1 (ginfer_read t))) 
 (assert (rinwms_display2 done))
 )

(defrule grassrun_rinwms_display3 (rinwms_display2 done) => 
 (python-call grass_message "** RHS: r.in.wms display cleanup **") 
 (python-call grass_run_command d.mon stop=x0)
 (assert (rinwms_display_shutdown done))
)

(defrule grassrun_rinwms_display4 (rinwms_display_shutdown done) => 
  (python-call grass_message "** RHS: r.in.wms purge raster **") 
  (python-call grass_run_command g.remove rast=rhs_srtm)
  (assert (rinwms_gremove done))
  )

; g.remove akl_srtm.2
; g.rename rast=akl_srtm.1,rhs_strm
; r.colors rhs_srtm
; d.mon d.rast
; g.erase rhs_srtm

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;; CLIPS TIME [WORKS]
; Muss noch angeschaltet werden !


;(defrule grassrun_timetest1 (timetest) => 
; (python-call grass_message "** RHS: TIMETEST 1 **") (bind ?early (time)) (ginfer_printout t "Before" ?early) (assert (timetest1)) (assert (timestamp ?early)))

;(defrule grassrun_timetest2 (timetest1) => 
; (python-call grass_message "** RHS: TIMETEST 2 **") (bind ?wait (time)) (ginfer_printout t "Now" ?later crlf) (assert (timetest2)))

;(defrule grassrun_timetest3 (timetest2) => 
; (python-call grass_message "** RHS: TIMETEST 3 **") (bind ?later (time)) (ginfer_printout t "Now" ?later crlf) (assert (timetest done)))

(deftemplate event (slot tstamp (default-dynamic (time))) (slot value))
; A template for the time-activated rules.
; Each instance consists of an automatically assigned timestamp and a user-assigned value

(defrule timedemo0 (time demo) => 
 (ginfer_printout t  " " crlf) 
 (ginfer_printout t "==========================================================================" crlf) 
 (ginfer_printout t "- CLIPS: Time-controlled Rule Demo" crlf)
 (ginfer_printout t "  Added value: Rules can have expiry dates and duration...." clrf)
 (ginfer_printout t  " " crlf) 
 (assert (start-time (time)))
)

(defrule time0
 (event (tstamp ?t1)(value 3))
 =>
 (ginfer_printout t "time0-rule: A value 3 event was detected. Its timestamp is=" ?t1 crlf)
 )

(defrule time1
 ?foo <- (event (tstamp ?t1)(value 3))
 ?now1 <- (time)
 ;(test (> (- ?now1 ?t1) 0.01))
 ;ES MAG ES NICHT WENN AUF DER LHS SCHON GETESTET WIRD ?!
 =>
 (retract ?foo)
 (ginfer_printout t "time1-rule: Retracting" ?t1 ?now1 crlf)
 )
 
 (defrule time4
 ?foo <- (event (tstamp ?t1)(value 3))
 (start-time ?t2)
 =>
 
 (ginfer_printout t "time4-rule: There is Value 3 Event of time #1. Current time is #2:" ?t1 ?t2 crlf)
 )

(defrule time2
 (time demo)
  =>
 (assert (event (value 3)))
 (ginfer_printout t "time2-rule: Event of value 3 created at time=" (time) crlf)
 )

(defrule time3
 ?foo <- (event (tstamp ?t1)(value 3))
 (start-time ?t2)
 ?now5 <- (time)
 ;(test (> (- ?t1 ?t2) 0.01))
 ;(test (> (- ?now5 ?t1) 0.01))
 ;ES MAG ES NICHT WENN AUF DER LHS SCHON GETESTET WIRD ?!

 =>
 (retract ?foo)
 (ginfer_printout t "time3-rule:  Value 3 Event has timestamp #1. Start time was #2. Now its #3 Retracting Event! " ?t1 ?t2 ?now5 crlf)
 )
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; RASTER MAPCALC [WORKS]

;(assert (raster demo))

(defrule grassrun_rmapcalc_random1 (raster demo) => (python-call grass_message "** RHS: r.mapcalc 1 **") (python-call grass_run_command "r.mapcalc" "rhs_mapcalc_1=rand(1,10)") (assert (mapcalc1 done)))

(defrule grassrun_rmapcalc_random2 (raster demo) => (python-call grass_message "** RHS: r.mapcalc 2 **") (python-call grass_run_command "r.mapcalc" "rhs_mapcalc_2=rand(1,2)") (assert (mapcalc2 done)))

; [r.surf.area] run

; [r.null] run

(defrule grassrun_rmapcalc1 (mapcalc1 done) (mapcalc2 done) => (python-call grass_message "** RHS: r.null **") (python-call grass_run_command r.null map=rhs_mapcalc_1 setnull=5) (assert (rnull done)))

; [r.patch] run
(defrule grassrun_rmapcalc2 (rnull done) => (python-call grass_message "** RHS: r.patch **") (python-call grass_run_command r.patch input=rhs_mapcalc_1,rhs_mapcalc_2 output=rhs_patch) (assert (rpatch done)))

(defrule grassrun_rmapcalc3 (rpatch done) => (python-call grass_message "** RHS: r.stats **") (python-call grass_run_command r.stats "c" input=rhs_patch) (assert (rnull done)))



;;;HIER FEHLT DIE VERKETTUNG ZU DEN FOLGENDEN RASTER-Subdemos

(defrule grassrun_gremove (rnull done) => (python-call grass_message "[RASTER DEMO]** RHS: g.remove cleanup **") (python-call grass_run_command g.remove rast=rhs_patch,rhs_mapcalc_1,rhs_mapcalc_2) (assert (gremove done)))

; [r.colors] run

;;;;;;;;;;;;;;;;;;;;;;;;;;
; [r.stats] run
;(defrule grassrun_rstats (verbose on) => (python-call grass_message "** RHS: r.stats run **") (python-call grass_run_command "r.stats" "cl" "input=geology" "fs=_"))

; [r.quantile] read

; [r.univar] read

; [r.what] read

;;;;;;;;;;;;;;;;;;;;;;;;;;
; [r.stats] read
(defrule grassread_rstats (verbose on) => (python-call grass_message "** RHS: r.stats read **") (bind ?result (python-call grass_read_command "r.stats" "cl" "input=geology" "fs=_")) (ginfer_printout t "===========" crlf)(ginfer_printout t ?result) (ginfer_printout t "===========" crlf))


;; export
;; -- file r.out.gdal
;; -- file r.in.gdal

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;## VECTOR

;;
;; v.in.external
;; v.in.region
;; v.random
;;
;;;;;;;;;;;;;;;;;;;;;;;;;;

;(assert (vector demo))
(defrule grassrun_vector1 
 (vector demo) => 
 (python-call grass_message "VECTOR DEMO:") 
 (python-call grass_message "** v.random **")  
 (python-call grass_run_command v.random output=rhs_random10 n=10) (assert (vrandom done))
)

(defrule grassrun_vector2 
  (vrandom done) => 
  (python-call grass_message "** v.info **") 
  (python-call grass_run_command v.info map=rhs_random10) 
  (assert (vinfo done)))

(defrule grassrun_vector2a 
  (vrandom done) => 
  (python-call grass_message "** v.stats **") 
 
  (python-call grass_run_command v.univar -ed map=rhs_random10)
  (assert (vunivar done)))


(defrule grassrun_vector3 
  (vinfo done) (vunivar done) => 
  (python-call grass_message "** g.remove vector **") 
  (python-call grass_run_command g.remove vect=rhs_random10) (assert (gremove_vect done)))

;; create empty vector
;; v.in.ascii 
;;
;; create empty vector with structure
;;
;; query vector
;; v.db.select READ
;; v.db.univar READ
;; v.distance
;; v.normal
;; v.univar READ
;;
;; modify vector ?
;; v.db.addtable
;; v.db.join
;; v.db.update
;; v.dissolve
;; v.generalize
;; v.patch
;; v.type
;; v.extract
;;
;; report on vector content
;;
;; report on vector topology
;;
;; convert vector (extract topo features)
;;
;;;; v.to.db
;; v.to.r3


;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; R.mapcalc-like rule concatenation:
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

;(assert (rmapcalc_rules demo))

(defrule rmapcalc_rules_01 
  (rmapcalc_rules demo) 
 => 
  (python-call grass_message "[rules like r.mapcalc] rule 01: Generate random GRASS raster by using r.mapcalc") 
  (python-call grass_run_command "r.mapcalc" "rmapcalc_rules_demo=rand(1,10)") 
  (assert (stages_mapcalc_01 done))
)
;Rule to create a new GRASS raster of random values

(deftemplate rmapcalc_rules_demo (slot x)(slot y)(slot value))
;Dummy template to ensure that the rules below will be parsed.

;^^^ Damit gibts die Probleme !!!
;**************************************
;**************************************
;**************************************

(defrule rmapcalc_rules_02 
  (stages_mapcalc_01 done) 
 => 
  (python-call grass_message "[rules like r.mapcalc] rule 02: Create CLIPS facts from GRASS raster layer") 
  (python-call grassraster2factlayer "rmapcalc_rules_demo" "the_comment" True False) 
  (assert (stages_ingest done))
)
;Rule import the new GRASS raster of random values into the CLIPS environment.

;(defrule rmapcalc_rules_03_preparation 
;  (stages_ingest done)
;  (not (trigger ?x ?y))
;  (not (completed ?x ?y))
;  (rmapcalc_rules_demo (x ?x) (y ?y) (value ?value)) 
;  ; DAS TEMPLATE wird erst angelegt wenn der GRASSRASTER_FACTLAYER eingeladen wird. Das ist nachdem diese Regel eingelesen wird.
;  ;Ein Mechanismus wird gebraucht um das generisch zu loesen -> Anlegen des Template explizit hier im Skript....
; => 
;  (python-call grass_message "[rules like r.mapcalc] rule 03: Generate Flag-facts for raster facts")
;  (assert (trigger ?x ?y))
;)
;; Rule to ensure that while for all facts created from the random raster layer there are (yet) no additional facs ("trigger"/"completed") sharing the same xy coordinate. While this applies (for all newly created raster-facts), an additional "trigger" fact is created for each coordinate tuple.

;(defrule rmapcalc_rules_04_execution 
;  ?thiscell <- (rmapcalc_rules_demo (x ?x) (y ?y) (value ?value)) 
;  ?thistrigger <- (trigger ?x ?y) (not (completed ?x ?y)) 
; => 
;  (python-call grass_message "[rules like r.mapcalc] rule 04: Increase each raster facts by 1000000; flag as done")
;  (modify ?thiscell (value (+ 100000 ?value))) 
;  (retract ?thistrigger) 
;  (assert (completed ?x ?y)))

;;;^^^ IF (aka: FOR ANY) there's a coordinate/location where there's a raster-layer-fact and a "trigger"-fact but no "completed"-fact, increase/MODIFY the attribute of the raster fact, remove the "trigger" fact and set a "completed" fact.

(undeftemplate rmapcalc_rules_demo)

; bzw: zwei verfahrenswege: 
; 1) einlesen, multiplikation * 10 im CLIPS space, export
; 2) zweiter RHS-rmapcalc aufruf zur multiplikation
; Zeiten vergleichen
; -> wenn Mapcalc versagt kann option 1) greifen !



	"""
    return payload

