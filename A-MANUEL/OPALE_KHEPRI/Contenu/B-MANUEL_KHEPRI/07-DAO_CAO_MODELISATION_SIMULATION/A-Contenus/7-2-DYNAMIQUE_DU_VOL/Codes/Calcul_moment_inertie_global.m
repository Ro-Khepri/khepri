clear all 
close all
clc;

%Calcul de la matrice d'inertie d'un parallépipède (L selon x, l selon y, h
%selon z)
prompt = 'Rentrer la valeur de la longueur ';
L = input(prompt);
prompt = 'Rentrer la valeur de la largeur ';
l = input(prompt);
prompt = 'Rentrer la valeur de la hauteur ';
h = input(prompt);
prompt = 'Rentrer la valeur de la masse ';
m = input(prompt);

I = zeros(3,3);
I(1,1) = l^2+h^2; 
I(2,2) = L^2+h^2;
I(3,3) = L^2+l^2;
I = (m/12)*I;
disp(I);

% Calcul de la matrice d'inertie d'un cône (axe y)
prompt = 'Rentrer la valeur de la hauteur ';
H = input(prompt);
prompt = 'Rentrer la valeur du rayon ';
R = input(prompt);
prompt = 'Rentrer la valeur de la masse ';
m = input(prompt);

C = zeros(3,3);
C(1,1) = (3/20)*m*R^2+(6/10)*m*H^2; 
C(2,2) = (3/10)*m*R^2;
C(3,3) = (3/20)*m*R^2+(6/10)*m*H^2;
disp(C);

Cg = zeros(3,3);
Cg(1,1) = C(1,1)+m*(H^2);
Cg(2,2) = C(2,2);
Cg(3,3) = C(3,3)+m*(H^2);
disp(Cg);


% % Calcul de la matrice d'inertie d'un cylindre (axe y)
% prompt = 'Rentrer la valeur de la hauteur ';
% Hauteur = input(prompt);
% prompt = 'Rentrer la valeur du rayon ';
% r = input(prompt);
% 
% Cy = zeros(3,3);
% Cy(1,1) = (3/20)*m*R^2+(6/10)*m*Hauteur^2; 
% Cy(2,2) = (3/10)*m*R^2;
% Cy(3,3) = (3/20)*m*R^2+(6/10)*m*Hauteur^2;
% disp(Cy);

% Calcul du centre de gravité(L selon x, l selon y, h selon z)
% prompt = 'Rentrer la valeur de la longueur ';
% L = input(prompt);
% prompt = 'Rentrer la valeur de la largeur ';
% l = input(prompt);
% prompt = 'Rentrer la valeur de la hauteur ';
% h = input(prompt);
% G=zeros(1,3);
% G(1,1) = L/2;
% G(1,2) = l/2;
% G(1,3) = h/2;
% disp(G)





