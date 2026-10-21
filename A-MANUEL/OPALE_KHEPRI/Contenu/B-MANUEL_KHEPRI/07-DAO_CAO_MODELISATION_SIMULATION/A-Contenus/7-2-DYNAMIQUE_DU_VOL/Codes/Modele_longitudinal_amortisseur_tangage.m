% Modèle longitudinal (mode d'oscillation d'incidence) du H201B Libelle et
% amortisseur de tangage (annexe 4 du rapport SFE 2023-02,
% SLT Pierre André Noël BOUASSE-BOU-KOMBILE-KOMBILE, juin 2023).
% Reconstitué depuis le PDF du rapport (aucun fichier source fourni) ; la ligne de
% commentaire « %M = ... », coupée en deux dans le PDF, a été rejointe.
% Nécessite la Control System Toolbox (ss, ss2tf, tf, rlocus, sisotool, impulse).
clear all; close all; clc;
% donnees de l'aeronef
M0 = 0;
CL_alphaW = 3.85;
CL_alphaH = 0.390;
B = 2.50;
Les = 0.421;
Le = 0.653;
MAC = Le
S = 9.8;
Mmax = 350;
i_2 = 1.05;
Vmax = 150/3.6;
rho = 1.225;
Lh = 5.515;%dist emp arriere
Lf = 1.896;%distance de la référence jusqu'au foyer de la voilure principale
Lb = 2.37% distance jusqu'au foyer de l'avion
Lcg = 1.944;% dist centre de gravité
xbarCG = (Lb - Lcg)/Le;
xbarAC_H = (Lcg - Lh)/Le;
xbarAC = (Lcg - Lf)/Le;
%Pression dynamique
qbar = 0.5*rho*Vmax^2
%Inertie du planeur
IyyB = sqrt(1.05)*Mmax;
%Surface de l'empennage
S_H = B*Le
% Moment Coefficient Sensitivity due to Pitch Rate
CMq = (-2*CL_alphaH)*(S_H/S)*((xbarAC_H - xbarCG)^2);
% Moment Coefficient Sensitivity due to Angle of Attack
CM_alpha = (CL_alphaW*(-xbarCG + xbarAC));
% Moment Coefficient Sensitivity due to Elevator
CM_deltaE = (-2*CL_alphaH)*(S_H/S)*(xbarAC_H - xbarCG);
% Moments
MTalpha = (qbar*S*Le*CM_alpha)/(IyyB); % (sec^-2)
Mq = ((qbar*S*Le*CMq)/(IyyB))*(Le/(2*Vmax)); % (sec^-1)
M_deltaE = (qbar*S*Le*CM_deltaE)/(IyyB); % (sec^-2)
% Total Moment / IyyB (= qdot)
%M = (M0 + CM_alpha * alpha + CM_q * q *(Le/(2*Vmax)) + CM_deltaE * deltaE)*qbar*S*MAC/(IyyB) ;
% Drag due to Airbrakes
%X_deltaAB = -(qbar*S*CD_deltaAB)/(Mmax); % (ft/sec^2)
% point de Vol
Ve = Vmax; % vitesse aero
he = 0; % altitude (attention negative par convention)
alphae = Mmax*9.81/(.5*rho*S*Ve^2)/CL_alphaW; % incidence (a l'equilibre)
% linear model : state-space (short period mode)
Zalpha = -CL_alphaW * 0.5* rho *S * Vmax^2/(Mmax*Vmax);
Malpha = CM_alpha*0.5*rho*S*Le*Vmax^2/IyyB
Aoi = [Zalpha, 1; Malpha, Mq];
Boi = [0; M_deltaE];
% deltaE -> q
SSAircraftOI = ss(Aoi,Boi,[0 1],0)
[NumTFAircraftOI,DenTFAircraftOI] = ss2tf(Aoi,Boi,[0 1],0);
TFAircraftOI = tf(NumTFAircraftOI,DenTFAircraftOI)
% pitch damper (amortisseur en tangage)
figure; rlocus(TFAircraftOI)
figure; sisotool(TFAircraftOI)
figure; impulse(TFAircraftOI)
kq=0.3; % pitch damper;
figure; impulse(TFAircraftOI/(1+kq*TFAircraftOI))
