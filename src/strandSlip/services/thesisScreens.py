"""What the six 1992 programs printed, FORMAT by FORMAT.

Each string is the FORMAT as the program's runtime saw it: for a WRITE with
the format in a character constant, its doubled quotes are single; a FORMAT
continued over several lines keeps the blanks that pad each line to column 72
where they matter (ECRZETA 41). The source file and line follow each one;
`tests/testServices/testThesisScreens.py` checks every one against the
recovered listings.
"""

from __future__ import annotations

from strandSlip.services.thesisSession import ThesisSession

# -- input (ENTHARD, ENTCONT, ENTZETA, ENSNHARD, ENSNCONT, ENSNZETA) -------------
radiusPrompt = "/,1X,'Entrez le rayon de courbure adim.:',\\"  # ENTHARD 34
radiusPromptContinuity = (  # ENTCONT 35
    "/,3X,'Entrez le rayon de courbure adim.',' (Valeur admissible 0.65<=>1.00):',\\"
)
radiusPromptCompliance = "/,3X,'Entrez le rayon de courbure adim.:',\\"  # ENTZETA 41
gammaPromptRadius = "/,3X,'Entrez le facteur complaisance GAM1:',\\"  # ENTZETA 38
noMacroSlipRadius = (  # ENTHARD 38, ENTCONT 41
    "//,1X,'Pas de macro-glissement dans la demi-pas ','XINF=',F5.2,1X,'a XSUP=',F5.2"
)
menuTitle = "/////////,3X,'Ce programme peut déterminer:'"  # ENSNHARD 19
menu = (  # ENSNHARD 21
    "////,6X,'1. La dissipation d énergie d un fil sur',' toute la longueur',/,8X,"
    "' d onde (pour THETAi=90 deg).',//,6X,'2. Le rapport relatif de différence maximale de'"
    ",/,9X,'déplacement (pour THETAi=0 deg).',//,6X,"
    "'3. Analyser un demi-pas en particulier (pour THETAi=90 deg).'"
)
choicePrompt = "///,9X,'Entrez votre choix:',\\"  # ENSNHARD 28
wavelengthPrompt = (  # ENSNHARD 35
    "/,9X,'Entrez un nombre pair de pas par longueur',' d onde:',\\"
)
amplitudePrompt = "/,9X,'Entrez l amplitude adimensionnelle:',\\"  # ENSNHARD 39
amplitudePromptContinuity = (  # ENSNCONT 40
    "/,9X,'Entrez l amplitude adimensionnelle',/,9X,'(Valeurs admissibles 1.0<=>1.5):',\\"
)
gammaPromptSinusoid = "/,9X,'Entrez le facteur de complaisance GAMMA1:',\\"  # ENSNZETA 43
turnsPrompt = "/,9X,'Nombre de tour de l origine (XTOUR) :',\\"  # HARDSIN 33
noMacroSlipSinusoid = (  # HARDSIN 55, CONTSIN 53
    "//,1X,'Pas de macro-glissement dans la demi pas ','XINF=',F5.2,1X,'a XSUP=',F5.2"
)
pressEnter = "Pressez ENTER pour continuer"  # PAUSE text

# -- manual approximations (PBCONV, CONTSIN, APPROX, APPSIN) ----------------------
boundsLine = "3X,'XINF= ',F5.2,3X,'XSUP=',F5.2,/"  # PBCONV 18, CONTSIN 70
lowerBoundPrompt = "/,3X,'Entrez l approx. de XB1:',\\"  # PBCONV 20, CONTSIN 72
upperBoundPrompt = "/,3X,'Entrez l approx. de XB2:',\\"  # CONTSIN 75
triedRadius = (  # APPROX 43
    "3X,'Valeur approximative de XB1C qui a ete ','essayee =',D16.8,/,"
    "3X,'Veuillez en rentrer une autre',' (devrait probablement etre inferieur)'"
)
triedSinusoid = (  # APPSIN 52
    "3X,'Valeur approximative de XB1C qui a été ','essayée =',D16.8,/,"
    "3X,'Veuillez en rentrer une autre',' (devrait probablement être inférieur)'"
)
approximationPrompt = "/,3X,'Entrez la nouvelle approximation de XB1C:',\\"  # APPROX 46

# -- Newton iterations (NEWT, NEWTON) ------------------------------------------------
convergenceProblem = (  # NEWT 56, NEWTON 93 and 108
    "///,1X,'!!!PROBLEME DE CONVERGENCE, ',/,1X,'Veuillez recommencer avec une nouvelle approx.',/"
)
iteration = "/,3X,'Iteration #',I2"  # NEWT 39, NEWTON 39
newtBounds = "3X,'XB1='D14.8,8X,'XB2=',D14.8,8X"  # NEWT 40
newtConstants = "3X,'XIC='D14.8,8X,'PSIC=',D14.8"  # NEWT 45
newtonBounds = "1X,'XB1='D16.8,5X,'XB2=',D16.8"  # NEWTON 40
newtonOffsets = "/,1X,'XB1-XINF='D14.8,4X,'XSUP-XB2=',D14.8"  # NEWTON 41
newtonPoints = "1X,'XK(',I2,')=',D16.8,5X,'XK(',I2,')=',D16.8"  # NEWTON 42
newtonPointOffsets = (  # NEWTON 43
    "1X,'XK(',I2,')-XINF=',D14.8,4X,'XSUP-XK(',I2,')=',D14.8"
)
portionsRadius = (  # ZETARHOB 20
    "//,3X,'Modèle à',I3,' port. liné; 2 delta max.=',F7.4,3X,'Valeur max adm.=',F7.4"
)
portionsSinusoid = (  # ZETASIN 20
    "//,3X,'Modele a',I3,' port. lin.; 2 delta max.=',F7.4,3X,'Valeur max adm.=',F7.4"
)
dmicroWarning = (  # DMICRO 27
    "///,1X,'ATTENTION! FUNCTION DMICRO:',2X,'la valeur =>',5X,F20.18,/,24X,"
    "'est change pour =>',5X,F20.18"
)

# -- results, constant radius (ECRHARD, ECRCONT, ECRZETA) ---------------------------
hardyTitle = "/,29X,'MODELE DE HARDY'"  # ECRHARD 16
continuityTitle = "/,18X,'MODELE AVEC CONTINUITE DE DEFORMATION'"  # ECRCONT 17
complianceTitle = "/,25X,'MODELE AVEC COMPLAISANCE'"  # ECRZETA 19
radiusSubtitle = "12X,'pour la flèche ayant un rayon de courbure ','constant'"  # ECRHARD 17
solutionRadius = "//,26X,'****** SOLUTION ******',/"  # ECRHARD 20
radiusParameters = (  # ECRHARD 21, ECRCONT 22
    "1X,'Pour le rayon de courbure constant adimension','nel =',F5.3,/,"
    "1X'avec la position initiale THETAi = ',F7.5,' rad. et',/,"
    "1X,'pour le demi-pas XINF =',F4.2,' à XSUP =',F4.2"
)
radiusParametersCompliance = (  # ECRZETA 24
    "1X,'Pour le rayon de courbure constant adimension','nel =',F5.3,/,"
    "1X,'avec un facteur de complaisance GAM1 =',F5.3,/,"
    "1X,'pour la position initiale THETAi = ',F7.4,' rad. et',/,"
    "1X,'le demi-pas XINF =',F4.2,' à XSUP =',F4.2"
)
fourUnknowns = "//,1X,'Les 4 inconnues sont:',/"  # ECRHARD 26
hardyUnknowns = "3X,'XB1=',D14.8,2X,'XB2=',D14.8,/,3X,'XIH=',D14.8,2X,'PSIH=',D14.8"  # 60
continuityUnknowns = "3X,'XB1=',D14.8,2X,'XB2=',D14.8,/,3X,'XIC=',D14.8,2X,'PSIC=',D14.8"
complianceUnknowns = "3X,'XB1=',D14.8,2X,'XB2=',D14.8,/,3X,'BTM=',D14.8,2X,'ETM=',D14.8"
resultsHeading = "//,1X,'Les résultats sont:'"  # ECRHARD 32
resultsHeadingCompliance = "///,1X,'Les résultats sont:'"  # ECRZETA 32
radiusResults = (  # ECRHARD 41, ECRCONT 41
    "/,3X,'Energie dissipée dans le demi-pas =',E14.8,/, 3X,'Rapport relatif de différence',"
    "' maximale de déplacement =',E14.8"
)
radiusResultsCompliance = (  # ECRZETA 41: two strings, the line padded to column 72 between
    "/,3X,'Energie dissipée dans le demi-pas =',E14.8,2X,'(Détails dans ENERGY.DAT)',/, "
    "3X,'Rapport relatif de différence',' maximale de déplacement =',E14.8,//,"
    "3X,'Les valeurs des '       'inconnues sont sauvegardées dans INCONNUS.DAT',/,"
)
profilePrompt = (  # ECRHARD 39, ECRCONT 40
    "/,3X,'Désirez-vous faire calculer le déplacement, la',' déformation et le rapport',/,"
    "3X,'de friction le',' long du demi-pas (0=>OUI, 1=>NON):',\\"
)
profilePromptCompliance = (  # ECRZETA 40, ECSNZETA 67
    "//,3X,'Désirez-vous faire calculer le déplacement,',' la déformation et le rapport',/,"
    "3X,'de friction le',' long du demi-pas (0=>OUI, 1=>NON):',\\"
)
profilePromptSinusoid = (  # ECSNHARD 55, ECSNCONT 55
    "////,3X,'Désirez-vous faire calculer le déplacement,',' la déformation et le rapport',/,"
    "3X,'de friction le',' long du demi-pas (0=>OUI, 1=>NON):',\\"
)

# -- results, sinusoid (ECSNHARD, ECSNCONT, ECSNZETA) ---------------------------------
sinusoidSubtitle = "24X,'pour la flèche sinusoidale'"  # ECSNHARD 21
solutionSinusoid = "/,26X,'****** SOLUTION ******',//"  # ECSNHARD 23
solutionSinusoidCompliance = "/,26X,'****** SOLUTION ******',/"  # ECSNZETA 25
solutionTotal = "//,26X,'****** SOLUTION ******',///"  # ECSNHARD 70
amplitudeParameters = (  # ECSNHARD 29, ECSNCONT 29
    "1X,'Pour l amplitude adimensionnelle =',F5.2,/,"
    "1X,'et un nombre de pas dans la longueur d onde =',F5.1,/,1X,"
    "'avec la position initiale THETAi = ',F7.5,' rad. et',/,"
    "1X,'pour le demi-pas XINF =',F5.2,' à XSUP =',F5.2"
)
amplitudeTotalParameters = (  # ECSNHARD 72, ECSNCONT 72
    "1X,'Pour l amplitude adimensionnelle =',F5.2,/,"
    "1X,'et un nombre de pas dans la longueur d onde =',F5.1,/,1X,"
    "'avec la position initiale THETAi = ',F7.5,' rad.',/////"
)
complianceParameters = (  # ECSNZETA 31
    "1X,'Pour l amplitude adimensionnelle =',F5.2,/,"
    "1X,'un nombre de pas dans la longueur d onde =',F5.1,/,1X,"
    "'et un facteur de complaisance GAMMA1 =',F5.3,/,1X,"
    "'avec la position initiale THETAi = ',F7.5,' rad. et',/,"
    "1X,'pour le demi-pas XINF =',F5.2,' à XSUP =',F5.2"
)
complianceTotalParameters = (  # ECSNZETA 86
    "1X,'Pour l amplitude adimensionnelle =',F5.2,/,"
    "1X,'un nombre de pas dans la longueur d onde =',F5.1,/,1X,"
    "'et un facteur de complaisance GAMMA1 =',F5.3,/,1X,"
    "'avec la position initiale THETAi = ',F7.5,' rad.',////"
)
fourUnknownsSinusoid = "/,1X,'Les 4 inconnues sont:',/"  # ECSNHARD 35
centralUnknowns = "/,1X,'Les 4 inconnues de la région centrale sont:',/"  # ECSNZETA 38
displacementRatio = (  # ECSNHARD 42
    "//, 1X,'et le rapport relatif de différence',' maximale de déplacement =',E14.8,//"
)
displacementRatioCompliance = (  # ECSNZETA 48
    "/, 1X,'et le rapport relatif de différence',' maximale de déplacement =',E14.8,//"
)
otherUnknowns = (  # ECSNZETA 46 and 65 (65 has a leading slash)
    "3X,'-> les valeurs des autres inconnues sont ','sauvegardées dans INCONNUS.DAT'"
)
halfPitchEnergy = "/,3X,'Energie dissipée dans le demi-pas =',E14.8,/"  # ECSNHARD 41
halfPitchEnergyCompliance = "/,3X,'Energie dissipée dans le demi-pas =',E14.8"  # ECSNZETA 41
seeEnergyFile = "3X,'(Voir ENERGY.DAT pour details)'"  # ECSNZETA 64
totalEnergy = (  # ECSNHARD 77
    "3X,'L énergie dissipée adimensionnelle totale',' par ce fil',/,"
    "3X,'tout le long de la longueur d onde = ',E14.8,//"
)

# -- profiles (SORTIE, SORTZETA) -------------------------------------------------------
profileHeading = (  # SORTIE 23, SORTZETA 36
    "///,1X,'POSITION EN X',9X,'DEP. FIL',11X,'DEF. FIL',8X,'RAP. DE FRICTION',/"
)
profileRow = "2X,F9.4,2X,3E20.8"  # SORTIE 10, SORTZETA 18
profileFileRow = "1X,F7.4,2X,E16.8,2X,E16.8"  # SORTIE 20
transitionRow = "2X,2E20.8"  # SORTZETA 22
portionOne = "2X,'PORTION #1'"  # SORTZETA 102 and 204
portionNumber = "2X,'PORTION #:',I2"  # SORTZETA 10
macroRegion = "2X,'REGION MACRO-GLISSMENT'"  # SORTZETA 152


def radiusResultScreen(
    session: ThesisSession, title: str, unknowns: str, values: tuple[float, ...], header
) -> None:
    """ECRHARD and ECRCONT up to the profile question; `header` is (RHOB, THETA, XINF, XSUP)."""
    session.write(title)
    session.write(radiusSubtitle)
    session.write(solutionRadius)
    session.write(radiusParameters, *header)
    session.write(fourUnknowns)
    session.write(unknowns, *values[:4])
    session.write(resultsHeading)
    session.write(radiusResults, *values[4:])


def sinusoidHalfPitchScreen(
    session: ThesisSession,
    title: str,
    firstBlankLines: str,
    unknowns: str,
    choice: int,
    header: tuple[float, ...],
    values: tuple[float, ...],
) -> None:
    """ECSNHARD and ECSNCONT for one half-pitch, up to the profile question.

    `header` is (ABAR, WLBAR, THETA, XINF, XSUP), `values` (XB1, XB2, XI, PSI, DSP, RDEP).
    """
    if choice in (2, 3):
        session.write(title)
        session.write(sinusoidSubtitle)
        session.write(solutionSinusoid)
    if choice == 1:
        session.write(firstBlankLines)
    session.write(amplitudeParameters, *header)
    session.write(fourUnknownsSinusoid)
    session.write(unknowns, *values[:4])
    if choice == 2:
        session.write(displacementRatio, values[5])
        return
    session.write(halfPitchEnergy, values[4])
    if choice == 1:
        session.write("///")


def sinusoidTotalScreen(session: ThesisSession, title: str, header, total: float) -> None:
    """The label-800 block of ECSNHARD and ECSNCONT: the energy over the wavelength."""
    session.write("///" + title.removeprefix("/"))
    session.write(sinusoidSubtitle)
    session.write(solutionTotal)
    session.write(amplitudeTotalParameters, *header)
    session.write(totalEnergy, total)


# -- ENERGY.DAT (DISPENRG) and INCONNUS.DAT (INCONNUS) ----------------------------------
energyHeading = "1X,'Energie dissipe dans chacune des regions du',' demi-pas:'"  # DISPENRG 33
energyRegion = "1X,'REG.',I3,'=',E16.8"  # DISPENRG 20
energyWithMacro = (  # DISPENRG 45
    "//,1X,'Energie dissipe dans tout le demi-pas=',E14.8,/,1X,'Total due au macro=',E14.8,/,"
    "1X,'Total due au micro=',E14.8,/,1X,'% due au macro=',F5.2,/,"
    "1X,'Energie dissipe dans la region de macro-glissement=',E14.8,/,"
    "1X,'Energie due au micro dans cette region=',E14.8,/1X,"
    "'% due au micro dans la region de macro=',F5.2"
)
energyMicroOnly = (  # DISPENRG 46
    "//,1X,'Il n y a que du micro-glissement dans ce demi-pas',/,"
    "1X,'Energie dissipe dans tout le demi-pas=',E14.8"
)
unknownsHeading = "1X,'Les paramètres imposés sont:'"  # INCONNUS 30
unknownsSinusoid = (  # INCONNUS 10, the block for the sinusoid
    "1X,'ABAR=',E14.8,2X,'WLBAR=',F9.6,2X,'GAM1=',E14.8,2X,'THETAi=',F9.6"
)
unknownsRadius = "1X,'GAM1=',E14.8,3X,'RHOB=',F9.6,3X,'THETAi=',F9.6"  # INCONNUS 10, commented
unknownsCounts = (  # INCONNUS 20
    "1X,'NPORTION=',I2,3X,'NPOINT=',I2,3X,'XINF=',D16.10,2X,'XSUP=',D16.10"
)
unknownsCurveHeading = "/,1X,'Les paramètres de complaisance sont:'"  # INCONNUS 45
unknownsCurve = (  # INCONNUS 25
    "1X,'XCOMP(',I2,')=',D14.9,2X,'YCOMP(',I2,')=',D14.9,2X,'ZETA(',I2,')=',D14.9"
)
unknownsCurveLast = "1X,'XCOMP(',I2,')=',D14.9,2X,'YCOMP(',I2,')=',D14.9"  # INCONNUS 26
unknownsListHeading = "/,1X,'Les inconnues sont:'"  # INCONNUS 54
unknownsLeft = "1X,'BETAG(',I2,')=',D16.10,2X,'ETAG(',I2,')=',D16.10"  # INCONNUS 30
unknownsRight = "1X,'BETAD(',I2,')=',D16.10,2X,'ETAD(',I2,')=',D16.10"  # INCONNUS 40
unknownsPoint = "1X,'XK(',I2,')=',D16.10"  # INCONNUS 50
unknownsCentre = "1X,'XB1=',D14.8,2X,'XB2=',D14.8,/,1X,'BTM=',D14.8,2X,'ETM=',D14.8"  # 60


def writeEnergyFile(session: ThesisSession, energy, regions: int) -> None:
    """ENERGY.DAT as DISPENRG wrote it; one or two regions skip its closing lines."""
    name = "ENERGY.DAT"
    session.openFile(name)
    session.writeFile(name, energyHeading)
    for number, value in energy.regions:
        session.writeFile(name, energyRegion, number, value)
    if regions < 3:
        return
    if energy.macroRegion is None:
        session.writeFile(name, energyMicroOnly, energy.total)
        return
    macro = energy.macroOnly
    session.writeFile(
        name,
        energyWithMacro,
        energy.total,
        macro,
        energy.microOnly,
        (macro / energy.total) * 100,
        energy.macroRegion,
        energy.microInMacro,
        (energy.microInMacro / energy.macroRegion) * 100,
    )


def writeUnknownsFile(
    session: ThesisSession, parameters: tuple[str, tuple[float, ...]], counts, curve, u
) -> None:
    """INCONNUS.DAT; `parameters` is the block for the deflection and its values,
    `counts` (NPORTION, NPOINT as set, XINF, XSUP)."""
    name = "INCONNUS.DAT"
    regions, printedPoints = counts[0], counts[1]
    session.openFile(name)
    session.writeFile(name, unknownsHeading)
    session.writeFile(name, parameters[0], *parameters[1])
    session.writeFile(name, unknownsCounts, *counts)
    session.writeFile(name, unknownsCurveHeading)
    for i in range(1, regions):
        session.writeFile(
            name, unknownsCurve, i, curve.xComp[i - 1], i, curve.yComp[i - 1], i, curve.zeta[i - 1]
        )
    last = regions - 1
    session.writeFile(
        name, unknownsCurveLast, regions, curve.xComp[last], regions, curve.yComp[last]
    )
    session.writeFile(name, unknownsListHeading)
    for i in range(1, regions):
        session.writeFile(name, unknownsLeft, i, u.betaLeft[i - 1], i, u.etaLeft[i - 1])
    session.writeFile(name, "/")
    for i in range(1, regions):
        session.writeFile(name, unknownsRight, i, u.betaRight[i - 1], i, u.etaRight[i - 1])
    session.writeFile(name, "/")
    for i in range(1, printedPoints + 1):
        session.writeFile(name, unknownsPoint, i, u.points[i - 1])
    session.writeFile(name, "/")
    session.writeFile(name, unknownsCentre, u.lowerBound, u.upperBound, u.centerBeta, u.centerEta)
