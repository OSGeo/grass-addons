#!/usr/bin/env python
############################################################################
#
# MODULE:       r.in.drsa
# AUTHOR:       Gianluca Massei - Antonio Boggia
# PURPOSE:      Import roles from *.rls file and apply those condition
#               at geographics information system for generate a raster
#               map classified under Dominance Rough Set Approach
# COPYRIGHT:    c) 2010 Gianluca Massei, Antonio Boggia  and the GRASS 
#               Development Team. This program is free software under the 
#               GNU General PublicLicense (>=v2). Read the file COPYING 
#               that comes with GRASS for details.
#
#############################################################################


#%Module
#% description: Generate a raster map classified with Dominance Rough Set Approach. Use *.rls file from JAMM, 4eMka2 etc.
#% keywords: raster, Dominance Rough Set Approach
#% keywords: Multi Criteria Decision Analysis (MCDA)
#%End
#%option
#% key: input
#% type: string
#% gisprompt: old,file,input
#% description: File name with rules (*.rls)
#% required: yes
#%end
#%option
#% key: output
#% type: string
#% gisprompt: new_file,cell,output
#% description: output classified raster map
#% required: yes
#%end
#%flag
#% key:k 
#% description:file *.rls from software 4eMka2
#%end
#%flag
#% key:j 
#% description:file *.rls from software jMAF
#%end



import sys
import grass.script as grass
import pdb
import string

def parser_4eMka2_rule(tags):
    "parser file *.rls from 4eMka2 software and extract information for make new classified raster"
    rule=dict()
    rules_list=[]
    for t in tags:
        condition=[]
        decision=[]
        row=t.split()
        if(len(row)>0 and row[0]=="Rule"):
            #rules_list.append(row)
            i=row.index("=>")
            for j in range(2,i):
                 if( row[j]!="&"):
                     condition.append(row[j].strip('[,;]'))
            for j in range(i+1,len(row)-2):
                     decision.append(row[j].strip('[,;]'))
            rule={'id_rule':row[1].strip('[.;]'),
                  'condition':condition,
                  'decision':string.join(decision),
                  'support':int(row[-2].strip('[.,;]')),
                  'strength':row[-1].strip('[,:]')}
            rules_list.append(rule)
            
    rls = open('rules',"w")
    for l in rules_list:
        factor=l['decision'].strip('()').split(' ')
        rls.write('%s=%s %s \n' % (l['id_rule'],l['id_rule'], " ".join(factor))) 
    rls.close
    return rules_list
    
def parser_JAMM_rule(tags):
    "parser file *.rls from JAMM software and extract information for make new classified raster"

    
def parser_mapcalc(rules,i):
    "parser to build a formula to be included  in mapcalc command"
    mapalgebra="if("
    for j in rules[i]['condition'][:-1]:
        mapalgebra+= j + " && " 
    mapalgebra+=rules[i]['condition'][-1]+","+rules[i]['id_rule']+",null())"
    return mapalgebra

def clean_rules(rules):
    "cleans rules to no processed vaue from rules (eg = -> ==) "
    for i in range(len(rules)):
        for j in rules[i]['condition']:
            if (j.find("<=")!=-1):
                return 1
            elif (j.find("<=")!=-1):
                return 1
            elif (j.find("=")!=-1):
                j=j.replace("=","==")
                return 0
            else:
                return -1
        
            

def main():
    input_rules = options['input']
    outputMap = options['output']

    gregion = grass.region()
    nrows = gregion['rows']
    ncols = gregion['cols']
    ewres=int(gregion['ewres'])
    nsres=int(gregion['nsres'])
    
    input_rules=open(input_rules,"r")
    tags=input_rules.readlines()   
    
    rules=[]  #single rule (dictionary) in array
    maps=[]
    rules=parser_4eMka2_rule(tags)
##    clean_rules(rules)
    for i in range(len(rules)):
        mappa="rule"+rules[i]['id_rule']
        formula=parser_mapcalc(rules,i)
        grass.mapcalc(mappa +"=" +formula)
        maps.append(mappa)
        
    mapstring=",".join(maps)	
    
    for m in maps:
        grass.run_command("r.to.vect", overwrite='True', flags='s', input=m, output=m, feature='area')
        grass.run_command("v.db.addcol", map=m, columns='rule varchar(25)')
        grass.run_command("v.db.update", map=m, column='rule', value=m)
    grass.run_command("v.patch", overwrite='True', flags='e', input=mapstring, output=outputMap)
       
    grass.run_command("r.patch", input=maps,  flags='-o', output='rulesMap')
    grass.run_command("r.reclass", input='rulesMap', flags='-o',  output='roughMAP', rules='rules')
    grass.run_command("r.to.vect", input='roughMAP', flags='-o', output=outputMap, feature='area')
    
    grass.run_command("g.remove",  rast=mapstring)
    grass.run_command("g.remove",  vect=mapstring)
    grass.run_command("g.remove",  vect="rulesMap,roughMAP")
    
    input_rules.close()

if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())


