# -*- coding: utf-8 -*-

#######################################################################
### Reference Knowledgebase with Demos
#######################################################################

def knowledgebase():
    #this function returns a huge here document, which is ingested by CLIPS instead or in addition to an external rulebase.
    # the string contains a rulebase containing demo rule-based actions in GRASS.
    # Some of these actions require a specific GRASS LOcation and will refuse to work otherwise [tbd]

    payload="""
   (deffacts startup "Set the attract mode" (attract mode))
	(assert (attract mode))

(defrule welcome (declare (salience 100)) (attract mode)  => 
 (ginfer_printout t " " crlf)
 (ginfer_printout t "******************************************************" crlf)
 (ginfer_printout t "*** Welcome to the g.inferreference knowledgebase ***  " crlf)
 (ginfer_printout t "******************************************************" crlf)
 (ginfer_printout t " " crlf)
 (ginfer_printout t " " crlf)
 (ginfer_printout t "Available Demonstrations:" crlf)
 (ginfer_printout t " " crlf)
 (ginfer_printout t "[a]  Overview g.infer extensions to CLIPS" crlf)
 (ginfer_printout t "[b]  CLIPS output and user input" crlf)

 (ginfer_printout t "[c] Ordered Facts"  crlf)
 (ginfer_printout t "[d] tbd: Unordered Facts and Templates "  crlf)
 (ginfer_printout t "[e] tbd: LHS Variables / Pattern Matching"  crlf)
 (ginfer_printout t "[f] tbd: RHS Variables"  crlf)
 (ginfer_printout t "[g] tbd: Conditionals"  crlf)
 (ginfer_printout t "[h] tbd: Saving / loading of rules"  crlf)
 (ginfer_printout t "[i]- Time-enabled rules demo" crlf)
 (ginfer_printout t "[j] tbd: Salience"  crlf)
 (ginfer_printout t "[k] tbd: Modules to partition a rulebase"  crlf)
 (ginfer_printout t " " crlf)
 (ginfer_printout t "Please select a demo by entering its number/letter:" crlf)
 (ginfer_printout t " " crlf)
 (ginfer_printout t "Hint: this knowledgebase can be written to file using (save FILENAME) from the CLIPS prompt." crlf)

 (assert (demo_selection (ginfer_read t)))
 (assert (demo_selection_completed))
)

(defrule welcome_selection_01 (demo_selection_completed) (demo_selection a) => (ginfer_printout t "Selection= g.infer extensions overview" crlf)(assert (g.infer commands)))
(defrule welcome_selection_04 (demo_selection_completed) (demo_selection b) => (ginfer_printout t "Selection= CLI-based user input demo" crlf)(assert (readline demo)))
(defrule welcome_selection_04 (demo_selection_completed) (demo_selection c) => (ginfer_printout t "Selection= CLI-based user input demo" crlf)(assert (orderedfacts demo)))



(defrule welcome_selection_05 (demo_selection_completed) (demo_selection 5) => (ginfer_printout t "Selection= CLIPS time-enabled rules demo" crlf)(assert (time demo)))
(defrule welcome_selection_06 (demo_selection_completed) (demo_selection 6) => (ginfer_printout t "Selection= Raster processing demo" crlf)(assert (raster demo)))
(defrule welcome_selection_07 (demo_selection_completed) (demo_selection 7) => (ginfer_printout t "Selection= Vector processing demo" crlf)(assert (vector demo)))
(defrule welcome_selection_08 (demo_selection_completed) (demo_selection 8) => (ginfer_printout t "Selection= GRASS location/region demo" crlf)(assert (region demo)))
(defrule welcome_selection_09 (demo_selection_completed) (demo_selection 9) => (ginfer_printout t "Selection= bootstrap loader demo" crlf)(assert (bootstrap demo)))
(defrule welcome_selection_A (demo_selection_completed) (demo_selection A) => (ginfer_printout t "Selection= Cellular automata demo" crlf)(assert (ca demo)))
(defrule welcome_selection_B (demo_selection_completed) (demo_selection B) => (ginfer_printout t "Selection= R.mapcalc analogue demo" crlf)(assert (rmapcalc_rules demo)))
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
(ginfer_printout t "" crlf)
(ginfer_printout t "" crlf)
(ginfer_printout t "[ *** Hit return, please *** ]" crlf)
(assert (userfeedback (ginfer_read t)))
;(reset)
;(run)
; doesn't work
)


;;;AUSSTEHEND:

; #clips.RegisterPythonFunction(grass.raster_info)
; #clips.RegisterPythonFunction(LOADFACTS)
; #clips.RegisterPythonFunction(ASSERT_RASTER_METADATA)
; #clips.RegisterPythonFunction(DATENBANKZEUGS)
; #clips.RegisterPythonFunction(MAPCALC)
; #clips.RegisterPythonFunction("GRASS_LAMBDA")


;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;READ and PRINT DEMO [WORKS]
(defrule readline_test0 (readline demo) => 
 (ginfer_printout t "[READ/PRINT #00]...Readline test begins..." crlf)
)

(defrule readline_test1 (readline demo) => 
 (ginfer_printout t "[READ/PRINT #01]: Enter your, please:" crlf)
 (assert (userfeedback (ginfer_read t)))
 (ginfer_printout t "[READ/PRINT #01]:  Thank you." crlf)
 (ginfer_printout t " " crlf)
)

(defrule readline_test2 (readline demo) (userfeedback ?feedback) => 
;What to do when ?feedback contains mutliple strings ?
 (ginfer_printout t "[READ/PRINT #02]: Your input:" $?feedback crlf)
; $? = multifield feedback
; ? = single field feedback
 (ginfer_printout t " " crlf)
 (ginfer_printout t "[READ/PRINT #02]: Enter RETURN to leave demo." crlf)
 (assert (ending (ginfer_read t)))
 (ginfer_printout t "[READ/PRINT #02] ========================= " crlf)
)

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;ORDERED FACTS [WORKS]

(defrule readline_of0 (orderedfacts demo) => 
 (ginfer_printout t "[ORDERED FACTS #00]... test begins..." crlf)
 (ginfer_printout t "[ORDERED FACTS #00]... asserting Duck fact: (duck quack)..." crlf)
 (assert (duck quack))
)

; (facts)
; (assert (a) (b) (c))
; (facts 0)
; (facts 2)


;STRINGS: "foo"
; (assert (duck "Joe")
; (assert (age 43)
; (assert (coordinates 11.1 22.4))
;Since spaces are used to separate multiple fields, it follows that spaces cannot simply be included in facts.
; (assert (double-quote "\"duck\""))


; retract a fact by its number:
;(retract 2)
; (retract 0 2)  all facts between 0 - 2
; (retract *) ;retract all

; Before a fact can be retracted, it must be specified to CLIPS. To retract a fact from a rule, the fact-address ; first must be bound to a variable on the LHS.
; (defrule get-married    ?duck <- (bachelor Dopey) =>    (printout t "Dopey is now happily married "  ?duck crlf)   (retract  ?duck))


;;;WILDCARDS
; The simplest form of wildcard is called a single-field wildcard and is shown by a question mark, "?". The "?" is also called a single-field constraint. A single‑field wildcard stands for exactly one field, as shown following.
; (defrule dating-ducks (bachelor Dopey ?)=>   (printout t "Date Dopey" crlf))

; multifield wildcard. This is a dollar sign followed by a question mark, "$?", and represents zero or more fields. Notice how this contrasts with the single-field wildcard which must match exactly one field.

;(defrule duck (animal-is duck) => (assert (sound-is quack)))
; (ppdefrule duck)

; (defrule duck (animal-is duck) => (printout t "quack" crlf))

;;CONDITIONALS/MATCHES
;(defrule take-a-vacation
;
;   (work done)                 ; Conditional element 1
;
;   (money plenty)              ; Conditional element 2
;
;   (reservations made)         ; Conditional element 3
;=>
;   (printout t "Let's go!!!" crlf))

;;;;;;;;;;;;;;
;assert-string                       Performs a string assertion by taking a string as argument and asserted as ;a nonstring fact.

;str-cat                                   Constructs a single-quoted string from individual items by string ;concatenation

;str-index                               Returns a string index of first occurrence of a substring

;sub-string                             Returns a substring from a string.

;str-compare                        Performs a  string compare

;str-length                              Returns the string length which is the length of a string:

;sym-cat                                Returns a concatenated symbol.
;;;;;;;;;;;;;;;;;;

;Asserting of Variables:
;(defrule make-quack   (duck-sound ?sound) =>   (assert (sound-is ?sound)))

; The first time a variable is bound it retains that value only within the rule, both on the LHS and also on the RHS, unless changed on the RHS.

 
;;;;;;;;;;;;;;CONSTRAINTS
; A way of handling this case is to use a field constraint to restrict the values that a pattern may have on the LHS. The field constraint acts like constraints on patterns.

;One type of field constraint is called a connective constraint. There are three types of connective constraints. The first is called a ~ constraint. Its ;symbol is the tilde "~". The ~ constraint acts on the one value that immediately follows it and will not allow that value.

;The second connective constraint is the bar constraint, "|". The "|" connective constraint is used to allow any of a group of values to match.
; (defrule cautious   (light yellow|blinking-yellow) =>   (printout t "Be cautious" crlf))

;The third type of connective constraint is the & connective constraint. The symbol of the & connective constraint is the ampersand, "&". The & constraint forces connected constraints to match in union.The & constraint normally is used only with the other constraints, otherwise it's not of much practi­cal use. 
;As an example, suppose you want to have a rule that will be triggered by a yellow or blinking-yellow fact. 
; That's easy enough—j­ust use the | connective constraint as you did in a previous example. 
; But suppose that you also want to identify the light color?
; The solution is to bind a variable to the color that is matched using the "&" and then print out the variable.
;(defrule cautious   (light ?color&yellow|blinking-yellow) =>   (printout t "Be cautious because light is " ?color crlf))

;The variable ?color will be bound to whatever color is matched by the field yellow|blinking-yellow.
;
;The "&" also is useful with the "~". For example, suppose you want a rule that triggers when the light is not yellow and not red.
; (defrule not-yellow-red   (light ?color&~red&~yellow)=>   (printout t "Go, since light is " ?color crlf))


;;NUMBERS

;CLIPS provides basic arithmetic and math functions +, /, *, -, div, max, min, abs, float, and integer. For more details, see the CLIPS Reference Manual.

;  Functions can be used on the LHS and the RHS. For example, the following shows how the arithmetic operation of addition is used on the RHS of a rule to assert a fact containing the sum of two numbers ?x and ?y.

;;(defrule addition (numbers ?x ?y) =>  (assert (answer-plus (+ ?x ?y))))     ; Add ?x + ?y

;A function can be used on the LHS if an equal sign, =, is used to tell CLIPS to evaluate the following expression rather than use it literally for pattern matching. 
;The following example shows how the hypotenuse is calculated on the LHS and used to pattern match against some stock items. 
;The exponentiation, "**", function is used to square the x and y values. 
;The first argument of exponentiation is the number which is to be raised to the power of the second argument.
;(defrule addition (numbers ?x ?y) (stock ?ID =(sqrt (+ (** ?x 2) (** ?y 2)))) ; Hypotenuse
;=>
;   (printout t "Stock ID=" ?ID crlf))


;(assert (answer-plus (+ ?x ?y ?z))))       ; ?x + ?y + ?z

;  (+ 2 2.0)     ; mixed arguments give float result
; (+ 2 2)       ;both integer arguments give integer
; (integer (+ 2.0 2.0))   ; convert float to integer
; (float (+ 2 2))         ;convert integer to float


;;;;;;;;;;;;TEST CONDITIONAL ELEMENT
;The test conditional element provides a very powerful way by which to compare numbers, variables, and strings on the LHS. 
;The (test) is used as a pattern on the LHS. A rule will only be triggered if the (test) is satisfied together with other patterns.

Logical: not an or
Arithmetic: / * + -
Comparison: any tpye: eq neq  numeric:  = <> <= >= > <

; A predicate function is one which returns a FALSE or a non-FALSE value. The colon ":" followed by a predicate function is called a predicate constraint. The ":" may be preceded by "&", "|", or "~" or may stand by itself as in the pattern (fact :(> 2 1)). It is typically used with the & connective constraint as "&:"

;(evenp <arg>)                      even number
;(floatp <arg>)                       floating-point number
;(integerp <arg>)                  integer
;(lexemep <arg>)                 symbol or string
;(numberp <arg>)                 float or integer
;(oddp <arg>)                        odd number
;(pointerp <arg>)                  external address
;(sequencep <arg>)             multifield value
;(stringp <arg>)                    string
;(symbolp <arg>)                 symbol


 ;;;EVAL / BUILD 
;The evaluation function, eval, is used for evaluating any string or symbol except the "def" type constructs such as defrule, deffacts, etc.,  as if entered ;at the top‑level. The build function takes care of the "def" type constructs. The (build) function is the complement of (eval). The build function evaluates ;a string or symbol as if it were entered at the top-level and returns TRUE if the argument is a legal def-type construct such as (defrule), (deffacts), and ; ;so forth.

;;;;;;;;BINDING VARIABLES
; The analog to assigning a value to a variable on the LHS by pattern matching is binding a value to a variable on the RHS using the bind function. It's convenient to bind variables on the RHS if the same values will be repeatedly used.

;(defrule addition   (numbers ?x ?y)=>   (assert (answer (+ ?x ?y)))   (bind ?answer (+ ?x ?y))   (printout t "answer is " ?answer crlf))


;The following rule illustrates some variable bindings on the RHS. The multifield value function, create$, is used to create a multifield value.
; (bind ?duck-bachelors (create$ Dopey Dorky Dinky))

; WATCH STUFF
;(watch facts)

; (watch instances)        ; used with objects

; (watch slots)            ; used with objects

; (watch rules)

; (watch activations)

; (watch messages)         ; used with objects

; (watch message-handlers) ; used with objects

; (watch generic-functions)

; (watch methods)          ; used with objects

; (watch deffunctions)

; (watch compilations)     ; on by default

; (watch statistics)

; (watch globals)

; (watch focus)

; (watch all) 
; THERE IS A PROBLEM IN THE CURRENT SHELL (Feb 2013) WITH TH WATCH COMMANDS;
   
;CLIPS[2/1]> (assert (fpp ff))
;Traceback (most recent call last):
;  File "g.infer.clips_RC2_20130219.py", line 2902, in <module>
;    sys.exit(main())
;  File "g.infer.clips_RC2_20130219.py", line 2850, in main
;    clips_shell.Run()
;  File "g.infer.clips_RC2_20130219.py", line 2314, in Run
;    if tx: t = "%s\n" % tx.rstrip() + t
;TypeError: cannot concatenate 'str' and 'NoneType' objects


;DEFFACTS
; (deffacts walk "Some facts about walking"  (foo) (baz))
; (reset)
; -> damit die KB restarten.
; (undeffacts walk)       
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;BOOTSTRAP/LOAD TEST [BROKEN]
;tbd: einen rule-getriggerten load eines weiteren CLIPS (ASCII) programms - upload on demand. Wird das auch der rulebase zugefügt ?
;batchstar ?

;(python-call ingest_rulebase_file upload_test.clp)



;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;RASTER WMS Import [WORKS]

;; import
;; -- file r.in.gdal
; r.in.wms output=akl_srtm mapserver="http://onearth.jpl.nasa.gov/wms.cgi" -c layers=worldwind_dem format=geotiff style=short_int maxcols=100 maxrows=100

(defrule grassrun_rinwms (raster_wms demo) => (python-call grass_message "** RHS: r.in.wms **") (python-call grass_run_command r.in.wms "c" output=akl_srtm mapserver=http://onearth.jpl.nasa.gov/wms.cgi  layers=worldwind_dem format=geotiff style=short_int maxcols=100 maxrows=100) (assert (rinwms done)))

(defrule grassrun_rinwms_remove (rinwms done) => (python-call grass_message "** RHS: r.in.wms remove raster2 **") (python-call grass_run_command g.remove rast=akl_srtm.2) (assert (rinwms_remove done)))

(defrule grassrun_rinwms_rename (rinwms_remove done) => (python-call grass_message "** RHS: r.in.wms rename raster1 **") (python-call grass_run_command g.rename rast=akl_srtm.1,rhs_srtm) (assert (rinwms_rename done)))

(defrule grassrun_rinwms_display2 (rinwms_rename done) => (python-call grass_message "** RHS: r.in.wms display **") (python-call grass_run_command d.mon start=x0) (python-call grass_run_command d.rast map=rhs_srtm) (assert (rinwms_display1 done)))

(defrule grassrun_rinwms_display1 (rinwms_display1 done) => (ginfer_printout t "Demo: Feedback, please:" crlf) (assert (ducky1 (ginfer_read t))) (assert (rinwms_display2 done)))

(defrule grassrun_rinwms_display3 (rinwms_display2 done) => (python-call grass_message "** RHS: r.in.wms display cleanup **") (python-call grass_run_command d.mon stop=x0)(assert (rinwms_display_shutdown done)))

(defrule grassrun_rinwms_display4 (rinwms_display_shutdown done) => (python-call grass_message "** RHS: r.in.wms purge raster **") (python-call grass_run_command g.remove rast=rhs_srtm)(assert (rinwms_gremove done)))

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


;(defrule grassrun_timetest1 (timetest) => (python-call grass_message "** RHS: TIMETEST 1 **") (bind ?early (time)) (ginfer_printout t "Before" ?early) (assert (timetest1)) (assert (timestamp ?early)))
;(defrule grassrun_timetest2 (timetest1) => (python-call grass_message "** RHS: TIMETEST 2 **") (bind ?wait (time)) (ginfer_printout t "Now" ?later crlf) (assert (timetest2)))
;(defrule grassrun_timetest3 (timetest2) => (python-call grass_message "** RHS: TIMETEST 3 **") (bind ?later (time)) (ginfer_printout t "Now" ?later crlf) (assert (timetest done)))

(deftemplate event (slot tstamp (default-dynamic (time))) (slot value))

(assert (event (value 1)))

(defrule time1
 ?foo <- (event (tstamp ?t1)(value 3))
 (start-time ?t2)
 (test (> (- ?t1 ?t2) 0.01))
 =>
 (retract ?foo)
 (ginfer_printout t "TIME DEMO: Retracting" ?t1 ?t2 crlf)
 )

(defrule time2
 (time test)
  =>
 (assert (event (value 3)))
 (ginfer_printout t "TIME DEMO: Timing=ON" (time) crlf)
 )

(defrule launch_time_demo 
   (time demo) 
   => 
   (assert (event (value 2)))
   (assert (start-time (time)))
 )



;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; CELLULAR AGENTS
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;UHRWERK;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;
;; Erzeuge zwei Zustaende Tick und Tack
;; Das System pendelt zwischen diesen beiden Zustaenden
;; Die TACK Regel leistet Tick -> Tack
;; TICK leistet Tack -> Tick
;; Der Zaehler in Tack wird dabei herabgezaehlt (durch TACK). Bei O stoppt das System.
;; Die TACKTACK Regel erzeugt ein Rasterabbild, welches in GRASS die Zustaende darstellt
;; 
;;WICHTIG: AM BESTEN KEINE REGELN MIT SALIENCE KLEINER ALS 400 FUER DIE
;; AGENTEN SELBST HERSTELLEN (350 und 300 sind vergeben)
(deftemplate state (slot name) (slot active)(slot count))

(defrule CA_Demo_wind_up_clock 
  (ca demo) 
  =>
  (printout t "Cellular Automata Demo: Set up for 10 clicks " crlf)
  (assert (state (name tick)(active 1)(count 0)))
  (assert (state (name tack)(active 0)(count 10)))
  ; ^^^10 = 10 Lebenstakte
)
(defglobal MAIN ?*grass* = (create$ ))
;^^^ a globale variable for CellualrAutomata

(defrule tack_action (declare (salience 300))(state (name tack) (active 1) (count ?c&:(> ?c 0)))
	 => (printout t "[tack_action] count="?c crlf)
	 (if (neq ?*grass* (create$ )) then
	 (progn
         (printout t "[tack_action] *Writeout Opportunity*" crlf)
	 ;2013: (r.to.grass (str-cat "state."?c))
         ;2013: Gegen passende Funktion ersetzen.

	 ;(bind ?*grass* (create$ )) 
	 ;;Das Auskommentieren erhaelt die letzten Zustaende, also eine Zeitkarte der Entwicklung (gut fuer mobile Agenten die "Spuren" hinterlassen).
	 )))
	    ;Nulle GlobalVar fuer neuen Lauf
	    
(defrule tick_action (declare (salience 300))(state (name tick) (active 1) (count ?c))
	 => (printout t "[tick_action]: Slacking !" crlf))

(defrule to_tack  ?tack<-(state (name tack) (active 0) (count ?tackc&:(> ?tackc 0)))
	       ?tick<-(state (name tick) (active 1) (count ?tickc))
=> (modify ?tack (active 1) (count (- ?tackc 1)))
   (modify ?tick (active 0))
   (printout t "[tick]          tick->tack" crlf)
)

(defrule to_tick  ?tack<-(state (name tack) (active 1) (count ?tackc))
	       ?tick<-(state (name tick) (active 0) (count ?tickc))
=> (modify ?tack (active 0) )
   (modify ?tick (active 1) )
   (printout t "[tack]          tack->tick" crlf)
   ;(p (str-cat "sleep 0;")) ;;<<< does not work in g.infer
)

(defrule tack_completed 
         (declare (salience 300))
         (state (name tack) (active 1) (count ?c&:(> ?c 0)))
	 ;2013:  ?done <- (done (id ?id)(value ?x))
         ?done <- (done ?id ?value)
	 => 
	;2013: (printout t "[tackdone] TACK cleared:" ?id crlf)	
        (printout t "[tack_completed] TACK cleared"  crlf)	
	(retract ?done)
)
; DONE IST DER MAGISCHE KLEBER ZWISCHEN DEM UHRWERK UND DER ARBEITSEBENE.
; Sobald in einem Takt die CA ihre AUfgabe fertig haben setzen sie ein DONE mit iherer ID (oder Koorindaten?)
; Am Ende des Tack-Tackts werden die DONES entfernt und ie CA beginnen von neuem.
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;Conways Game of LIFE:
;; implemented as cellular automata (CA) in CLIPS
;; Original code by Peter Loewe, 2003
;;
;;
;; Examine each grid position and spawn/kill CA according to these rules:
;; Law 1: (alive self) AND "2 or 3" neighbours: CA lives on
;; Law 2: (alive self) AND "< 2 or >3" neighbours: CA dies
;; Law 3: (dead self) AND "==3" neighbours: New CA spawned

(deftemplate cell (slot x) (slot y) (slot id) (slot alive)(slot neighbours))
;Cellular agent (CA) definition template - the CA contains info about its position, its binary health (alive|dead) and the number of neighbours (which are alive, too) 

(defrule ca__set_neighbours_zero (declare (salience 450))
  ?this <-(cell (x ?x) (y ?y) (id ?id) (alive ?a)(neighbours ?n&:(> ?n 0)))
  =>
  (modify ?this (neighbours 0))
)
; Rule to reset the number of known neighbours in a CA.

(defrule east (declare (salience 400))
  ?this <- (cell (x ?x) (y ?y) (id ?id) (alive ?a)(neighbours ?n))
  ;(cell (x ?nx&:(= ?nx (+ ?x 1))) (y ?ny)(id ?nid) (alive TRUE) (neighbours ?nn))
  ?alive <- (cell (x ?cx) (y ?cy) (id ?nid)(alive TRUE) (neighbours ?fuk))
  ;(cell (x ?x) (y ?ny&:(= (- ?ny ?y) -1))(id ?nid) (alive FALSE) (neighbours ?nn))
  (test (and (eq (+ ?x 1) ?cx) (eq ?y ?cy )))
 =>
  (printout t "yebo" crlf)
  (modify ?this (neighbours (+ 1 ?n)))
)
; Rule to test whether a CA is alive on the relative position "x+1" ("East")


(defrule west (declare (salience 420))
  ?this <-(cell (x ?x) (y ?y) (id ?id) (alive ?a)(neighbours ?n))
  (cell (x ?nx&:(= ?nx (- ?x 1))) (y ?ny) (id ?nid) (alive TRUE) (neighbours ?nn))
 =>
  (modify ?this (neighbours (+ 1 ?n)))
)
; Rule to test whether a CA is alive on the relative position "x-1" ("West")

(defrule north (declare (salience 420))
  ?this <-(cell (x ?x) (y ?y) (id ?id) (alive ?a)(neighbours ?n))
  (cell (x ?nx) (y ?ny&:(= ?ny (+ ?y 1))) (id ?nid) (alive TRUE) (neighbours ?nn))
 =>
  (modify ?this (neighbours (+ 1 ?n)))
)
; Rule to test whether a CA is alive on the relative position "y+1" ("North")

(defrule south (declare (salience 420))
  ?this <-(cell (x ?x) (y ?y)(id ?id)  (alive ?a)(neighbours ?n))
  (cell (x ?nx) (y ?ny&:(= ?ny (- ?y 1))) (id ?nid)(alive TRUE) (neighbours ?nn))
 =>
  (modify ?this (neighbours (+ 1 ?n)))
)
; Rule to test whether a CA is alive on the relative position "y-1" ("South")

(defrule southwest  (declare (salience 420))
?this <-(cell (x ?x) (y ?y)(id ?id)  (alive ?a)(neighbours ?n))
(cell (x ?nx&:(= ?nx (- ?x 1))) (y ?ny&:(= ?ny (- ?y 1))) (id ?nid)(alive TRUE) (neighbours ?nn))
=>
(modify ?this (neighbours (+ 1 ?n)))
)
; Rule to test whether a CA is alive on the relative position "x-1, y-1" ("Southwest")

(defrule southeast  (declare (salience 420))
  ?this <-(cell (x ?x) (y ?y)(id ?id)  (alive ?a)(neighbours ?n))
  (cell (x ?nx&:(= ?nx (+ ?x 1))) (y ?ny&:(= ?ny (- ?y 1))) (id ?nid)(alive TRUE) (neighbours ?nn))
 =>
  (modify ?this (neighbours (+ 1 ?n)))
)
; Rule to test whether a CA is alive on the relative position "x+1, y-1" ("Southeast")

(defrule northwest  (declare (salience 420))
  ?this <-(cell (x ?x) (y ?y)(id ?id)  (alive ?a)(neighbours ?n))
  (cell (x ?nx&:(= ?nx (- ?x 1))) (y ?ny&:(= ?ny (+ ?y 1))) (id ?nid)(alive TRUE) (neighbours ?nn))
 =>
 (modify ?this (neighbours (+ 1 ?n)))
)
; Rule to test whether a CA is alive on the relative position "x-1, y+1" ("Northwest")

(defrule northeast  (declare (salience 420))
  ?this <-(cell (x ?x) (y ?y)(id ?id)(alive ?a)(neighbours ?n))
  (cell (x ?nx&:(= ?nx (+ ?x 1))) (y ?ny&:(= ?ny (+ ?y 1))) (id ?nid)(alive TRUE) (neighbours ?nn))
 =>
  (modify ?this (neighbours (+ 1 ?n)))
)
; Rule to test whether a CA is alive on the relative position "x-1, y-1" ("Northeast")

(defrule conway_law1 (declare (salience 410))
  ?this <- (cell (x ?x) (y ?y) (id ?id) (alive TRUE) (neighbours ?n&:(and (>= ?n 2) (<=  ?n 3))))
 =>
  ;2013: (assert (done (id ?id)(value TRUE)))
  (assert (foo 2013))
)
; Conway's Life Law 1: CA has 2 - 3 neighbours and survives.

(defrule conway_law2 (declare (salience 410))
  ?this <- (cell (x ?x) (y ?y) (id ?id) (alive TRUE) (neighbours ?n&:(or (< ?n 2) (> ?n 3))))
 =>
  ;2013: (assert (done (id ?id)(value FALSE)))
  (assert (done ?id FALSE))
  (modify ?this (alive FALSE))
)
; Conway's Life Law 2: CA has less than 2 or more than 3 neighbours and dies.

(defrule conway_law3 (declare (salience 410))
  ?this <- (cell (x ?x) (y ?y) (id ?id) (alive FALSE) (neighbours ?n&: (= ?n 3)))
 =>
  ;2013: (assert (done (id ?id)(value TRUE)))
  (assert (done ?id TRUE))
  (modify ?this (alive TRUE))
)
; Conway's Life Law 3: A new CA is spawned at an empty location with 3 neighbours.

(defrule dead (declare (salience 410))
   (cell (x ?x) (y ?y) (id ?id)(alive FALSE) (neighbours ?n)) 
  =>
   (bind ?*grass* (create$ ?*grass* (format nil "%f %f 0" ?x ?y)) ) 
)
; rule to printout the coordinates of an deceased CA

(defrule alive (declare (salience 410))
   (cell (x ?x) (y ?y) (id ?id)(alive TRUE) (neighbours ?n)) 
  => 
   (bind ?*grass* (create$ ?*grass* (format nil "%f %f 100" ?x ?y)) ) 
)
; rule to printout the coordinates of an alive CA  

(defrule CA_2013 
  (ca demo DEACTIVATED) ; derzeit gehts in einen infinity loop! 
 => 
  (assert (cell (x 0) (y 0) (id (gensym*)) (alive FALSE) (neighbours 0)))
  (loop-for-count (?x 0 5)
	(loop-for-count (?y 0 5)
	(assert (cell (x ?x) (y ?y) (id (gensym*)) (alive FALSE) (neighbours 0)))
		))
  ;;Loop to create CA from template for coordinates (x:[0-5] y:[0-5])

  (assert (cell (x 1) (y 5) (id (gensym*)) (alive TRUE) (neighbours 0)))
  (assert (cell (x 5) (y 5) (id (gensym*)) (alive TRUE) (neighbours 0)))
  (assert (cell (x 1) (y 4) (id (gensym*)) (alive TRUE) (neighbours 0)))
  (assert (cell (x 2) (y 4) (id (gensym*)) (alive TRUE) (neighbours 0)))
  (assert (cell (x 3) (y 4) (id (gensym*)) (alive TRUE) (neighbours 0)))
  (assert (cell (x 4) (y 4) (id (gensym*)) (alive TRUE) (neighbours 0)))
  (assert (cell (x 1) (y 3) (id (gensym*)) (alive TRUE) (neighbours 0)))
  (assert (cell (x 5) (y 3) (id (gensym*)) (alive TRUE) (neighbours 0)))
  (assert (cell (x 4) (y 3) (id (gensym*)) (alive TRUE) (neighbours 0)))
  ;;Explicit spawning of 9 CA on the 25 field "grid"
)

(defrule unify
  ?dead <- (cell (x ?x) (y ?y) (id ?id)(alive FALSE) (neighbours 0))
  ?alive <- (cell (x ?x) (y ?y) (id ?nid)(alive TRUE) (neighbours 0))
=>
  (printout t ?x" "?y crlf)
  (retract ?dead)
)
;Rule to overwrite dead/nonexistent CA with new/alive ones: 
; If both a dead and an alive CA exist for the same coordinate, the dead one is retracted. 

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; R.mapcalc-like rule concatenation:
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

;(assert (rmapcalc_rules demo))

(defrule rmapcalc_rules_01 
  (rmapcalc_rules demo) 
 => 
  (python-call grass_message "[rules like r.mapcalc] rule 01: Generate random GRASS raster") 
  (python-call grass_run_command "r.mapcalc" "rmapcalc_rules_demo=rand(1,10)") 
  (assert (stages_mapcalc done))
)
;Rule to create a new GRASS raster of random values


(deftemplate rmapcalc_rules_demo (slot x)(slot y)(slot value))
;Dummy template to ensure that the rules below will be parsed.

(defrule rmapcalc_rules_02 
  (stages_mapcalc done) 
 => 
  (python-call grass_message "[rules like r.mapcalc] rule 02: Create CLIPS facts from GRASS raster layer") 
  (python-call grassraster2factlayer "rmapcalc_rules_demo" "the_comment" True False) 
  (assert (stages_ingest done))
)
;Rule import the new GRASS raster of random values into the CLIPS environment.

(defrule rmapcalc_rules_03_preparation 
  (stages_ingest done)
  (not (trigger ?x ?y))
  (not (completed ?x ?y))
  (rmapcalc_rules_demo (x ?x) (y ?y) (value ?value)) 
  ; DAS TEMPLATE wird erst angelegt wenn der GRASSRASTER_FACTLAYER eingeladen wird. Das ist nachdem diese Regel eingelesen wird.
  ;Ein Mechanismus wird gebraucht um das generisch zu loesen -> Anlegen des Template explizit hier im Skript....
 => 
  (python-call grass_message "[rules like r.mapcalc] rule 03: Generate Flag-facts for raster facts")
  (assert (trigger ?x ?y))
)
; Rule to ensure that while for all facts created from the random raster layer there are (yet) no additional facs ("trigger"/"completed") sharing the same xy coordinate. While this applies (for all newly created raster-facts), an additional "trigger" fact is created for each coordinate tuple.

(defrule rmapcalc_rules_04_execution 
  ?thiscell <- (rmapcalc_rules_demo (x ?x) (y ?y) (value ?value)) 
  ?thistrigger <- (trigger ?x ?y) (not (completed ?x ?y)) 
 => 
  (python-call grass_message "[rules like r.mapcalc] rule 04: Increase each raster facts by 1000000; flag as done")
  (modify ?thiscell (value (+ 100000 ?value))) 
  (retract ?thistrigger) 
  (assert (completed ?x ?y)))

;;;^^^ IF (aka: FOR ANY) there's a coordinate/location where there's a raster-layer-fact and a "trigger"-fact but no "completed"-fact, increase/MODIFY the attribute of the raster fact, remove the "trigger" fact and set a "completed" fact.

(undeftemplate rmapcalc_rules_demo)

; bzw: zwei verfahrenswege: 
; 1) einlesen, multiplikation * 10 im CLIPS space, export
; 2) zweiter RHS-rmapcalc aufruf zur multiplikation
; Zeiten vergleichen
; -> wenn Mapcalc versagt kann option 1) greifen !



	"""
    return payload

