# Original archived author Ebro input deltas

## Ebro_evol.PRM
--- 2017/Ebro_evol.PRM
+++ 2026/Ebro_evol.PRM
@@ -11,8 +11,8 @@
 
 version		TISC_2016-08-30
 
-Nx             	104
-Ny             	55
+Nx             	208
+Ny             	110
 
 xmin           	-48160
 xmax           	660573
@@ -23,7 +23,7 @@
 Timefinal      	-0
 dt             	.5
 dt_record      	0
-dt_eros        	.025
+dt_eros        	.05
 
 random_topo    	5
 
@@ -58,5 +58,5 @@
 
 switch_sea     	1
 switch_files   	1
-switch_ps      	1
+plotting_mode	2	For svg/postscript output.
 verbose_level  	1

