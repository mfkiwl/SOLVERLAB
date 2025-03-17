# -*-coding:utf-8 -*
#===============================================================================================================================
# Name        : Résolution EF avec quadrature aux faces de l'équation de Poisson 2D -\triangle u = f avec f raide
# Author      : Michaël Ndjinga
# Copyright   : CEA Saclay 2025
# Description : Utilisation d'une quadrature du second ordre pour la discrétisation de f sur un triangle ABC :
#                 \int f = 1/3 ( f(AB)+f(BC)+f(AC) ) * |ABC|
#               Utilisation de la méthode des éléménts finis P1 avec champs u discrétisé aux noeuds (et f aux faces) d'un maillage triangulaire
#               Création et sauvegarde du champ résultant ainsi que du champ second membre en utilisant la librairie CDMATH
#               Comparaison de la solution numérique avec la solution exacte u = x*(1-x)*y*(1-y)*tanh(alpha * (y - x))
#================================================================================================================================

import cdmath
from math import tanh 

#parameter of the stiffness of the exact solution
alpha = 10

def right_hand_side(x, y):
    A = x*(1-x)*y*(1-y)
    B = tanh(alpha * (y - x))

    dAx = (1-x)*y*(1-y) - x*y*(1-y)
    dAxx = -2*y*(1-y)
    dAy = x*(1-x)*(1-y) - x*(1-x)*y
    dAyy = -2*x*(1-x)

    dBx = alpha * (B**2 - 1)
    dBxx = 2*alpha * dBx * B
    dBy = alpha * (1 - B**2)
    dByy = -2*alpha * dBy * B

    return dAxx*B+2*dAx*dBx+A*dBxx + dAyy*B+2*dAy*dBy+A*dByy

def exact_solution(x, y):

    A = x*(1-x)*y*(1-y)
    B = tanh(alpha * (y - x))

    return -A*B

#Chargement du maillage triangulaire du domaine carré [0,1]x[0,1], définition des bords
#=======================================================================================
my_mesh = cdmath.Mesh("squareWithTriangles.med")
if( my_mesh.getSpaceDimension()!=2 or my_mesh.getMeshDimension()!=2) :
    raise ValueError("Wrong space or mesh dimension : space and mesh dimensions should be 2")
if(not my_mesh.isTriangular()) :
    raise ValueError("Wrong cell types : mesh is not made of triangles")

nbNodes = my_mesh.getNumberOfNodes()
nbCells = my_mesh.getNumberOfCells()
nbFaces = my_mesh.getNumberOfFaces()

print("Mesh loading done")
print("Number of nodes=", nbNodes)
print("Number of cells=", nbCells)

#Discrétisation du second membre et détermination des noeuds intérieurs
#======================================================================
my_RHSfield = cdmath.Field("RHS_field"     , cdmath.FACES, my_mesh, 1)
exact_sol   = cdmath.Field("Exact solution", cdmath.NODES, my_mesh, 1)
nbInteriorNodes = 0
nbBoundaryNodes = 0
maxNbNeighbours = 0#This is to determine the number of non zero coefficients in the sparse finite element rigidity matrix
interiorNodes=[]
boundaryNodes=[]

#parcours des noeuds pour extraction 1) des noeuds intérieur 2) des noeuds frontière 3) du nb max voisins d'un noeud
for i in range(nbNodes):
    Ni=my_mesh.getNode(i)
    x = Ni.x()
    y = Ni.y()

    exact_sol[i]  =exact_solution(x, y)#mettre la solution exacte
    
    if my_mesh.isBorderNode(i): # Détection des noeuds frontière
        boundaryNodes.append(i)
        nbBoundaryNodes=nbBoundaryNodes+1
    else: # Détection des noeuds intérieurs
        interiorNodes.append(i)
        nbInteriorNodes=nbInteriorNodes+1
        maxNbNeighbours= max(1+Ni.getNumberOfCells(),maxNbNeighbours) #true only in 2D, otherwise use function Ni.getNumberOfEdges()

print("nb of interior nodes=", nbInteriorNodes)
print("nb of boundary nodes=", nbBoundaryNodes)
print("Max nb of neighbours=", maxNbNeighbours)

#parcours des noeuds pour discrétisation du second membre 
for i in range(nbFaces):
    Fi=my_mesh.getFace(i)
    x = Fi.x()
    y = Fi.y()

    my_RHSfield[i]=right_hand_side(x, y)#mettre la fonction definie au second membre de l'edp

print("Right hand side discretisation done")

# Construction de la matrice de rigidité et du vecteur second membre du système linéaire
#=======================================================================================
Rigidite=cdmath.SparseMatrixPetsc(nbInteriorNodes,nbInteriorNodes,maxNbNeighbours)# warning : third argument is max number of non zero coefficients per line of the matrix
RHS=cdmath.Vector(nbInteriorNodes)

# Vecteurs gradient de la fonction de forme associée à chaque noeud d'un triangle (hypothèse 2D)
GradShapeFunc0=cdmath.Vector(2)
GradShapeFunc1=cdmath.Vector(2)
GradShapeFunc2=cdmath.Vector(2)

#On parcourt les triangles du domaine
for i in range(nbCells):

    Ci=my_mesh.getCell(i)

    #Contribution à la matrice de rigidité
    nodeId0=Ci.getNodeId(0)
    nodeId1=Ci.getNodeId(1)
    nodeId2=Ci.getNodeId(2)

    N0=my_mesh.getNode(nodeId0)
    N1=my_mesh.getNode(nodeId1)
    N2=my_mesh.getNode(nodeId2)

    #Formule des gradients voir EF P1 -> calcul déterminants
    GradShapeFunc0[0]= (N1.y()-N2.y())/2
    GradShapeFunc0[1]=-(N1.x()-N2.x())/2
    GradShapeFunc1[0]=-(N0.y()-N2.y())/2
    GradShapeFunc1[1]= (N0.x()-N2.x())/2
    GradShapeFunc2[0]= (N0.y()-N1.y())/2
    GradShapeFunc2[1]=-(N0.x()-N1.x())/2

    #Création d'un tableau (numéro du noeud, gradient de la fonction de forme
    GradShapeFuncs={nodeId0 : GradShapeFunc0}
    GradShapeFuncs[nodeId1]=GradShapeFunc1
    GradShapeFuncs[nodeId2]=GradShapeFunc2

    # Remplissage de  la matrice de rigidité et du second membre
    for j in [nodeId0,nodeId1,nodeId2] :
        if boundaryNodes.count(j)==0 : #seuls les noeuds intérieurs contribuent au système linéaire (matrice de rigidité et second membre)
            j_int=interiorNodes.index(j)#indice du noeud j en tant que noeud intérieur
            Nj=my_mesh.getNode(j)#Faire une boucle sur les faces de Ci et lire les valeurs stockées dans le champs RHS_field
            x = Nj.x()#Faire une boucle sur les faces de Ci et lire les valeurs stockées dans le champs RHS_field
            y = Nj.y()#Faire une boucle sur les faces de Ci et lire les valeurs stockées dans le champs RHS_field
            #Contribution de la cellule triangulaire i à la ligne j_int du système linéaire et j_int du second membre
            for k in [nodeId0,nodeId1,nodeId2] : 
                if boundaryNodes.count(k)==0 : #seuls les noeuds intérieurs contribuent à la matrice du système linéaire
                    k_int=interiorNodes.index(k)#indice du noeud k en tant que noeud intérieur
                    Rigidite.addValue(j_int,k_int,GradShapeFuncs[j]*GradShapeFuncs[k]/Ci.getMeasure())
                #else: si condition limite non nulle au bord, ajouter la contribution du bord au second membre de la cellule j
                #Ajout de la contribution du segment j-k au second membre du noeud j 
                if j!=k :#Faire une boucle sur les faces de Ci et lire les valeurs stockées dans le champs RHS_field
                    Nk=my_mesh.getNode(k)
                    x = (Nj.x()+Nk.x())/2
                    y = (Nj.y()+Nk.y())/2
                
                    #Quadrature d'ordre 2 :
                    rhsFace=right_hand_side(x, y)#Value at the face for the right hand side integral evaluation
                    RHS[j_int]+=Ci.getMeasure()/6*rhsFace # intégrale dans le triangle du produit f x fonction de base

print("Linear system matrix building done")

# Conditionnement de la matrice de rigidité
#=================================
cond = Rigidite.getConditionNumber()
print("Condition number is ",cond)

# Résolution du système linéaire
#=================================
LS=cdmath.LinearSolver(Rigidite,RHS,100,1.E-6,"CG","ILU")#Remplacer CG par CHOLESKY pour solveur direct
SolSyst=LS.solve()

print("Preconditioner used : ", LS.getNameOfPc())
print("Number of iterations used : ", LS.getNumberOfIter())
print("Final residual : ", LS.getResidu())
print("Linear system solved")

# Création du champ résultat
#===========================
my_ResultField = cdmath.Field("ResultField", cdmath.NODES, my_mesh, 1)
for j in range(nbInteriorNodes):
    my_ResultField[interiorNodes[j]]=SolSyst[j];#remplissage des valeurs pour les noeuds intérieurs
for j in range(nbBoundaryNodes):
    my_ResultField[boundaryNodes[j]]=0;#remplissage des valeurs pour les noeuds frontière (condition limite)
#sauvegarde sur le disque dur du résultat dans un fichier paraview
my_ResultField.writeVTK("FiniteElements2DPoisson_STIFFRHS_FACE_based_quadrature_ResultField")

exact_sol.writeVTK("FiniteElements2DPoisson_STIFFRHS_ExactSol")
my_RHSfield.writeVTK("FiniteElements2DPoisson_STIFFRHS_FACE_based_quadrature_RHS")

print("Numerical solution of 2D Poisson equation on a square using finite elements done")

#Calcul de l'erreur commise par rapport à la solution exacte + vérification du principe du maximum
#==================================================================================================
max_sol_num=my_ResultField.max()
min_sol_num=my_ResultField.min()
max_abs_sol_exacte=max(max_sol_num,-min_sol_num)
erreur_abs= (exact_sol - my_ResultField).normMax()[0]

print("Absolute error = max(| exact solution - numerical solution |)                         = ",erreur_abs )
print("Relative error = max(| exact solution - numerical solution |)/max(| exact solution |) = ",erreur_abs/max_abs_sol_exacte)
print("Maximum numerical solution = ", max_sol_num,     " Minimum numerical solution = ", min_sol_num)
print("Maximum exact solution     = ", exact_sol.max(), " Minimum exact solution     = ", exact_sol.min() )

assert erreur_abs/max_abs_sol_exacte <1.
