#!/usr/bin/env python3
from pathlib import Path
p=Path("src/brogue/Monsters.c")
s=p.read_text()
needle='obrienBashirReturnTurn = rogue.absoluteTurnNumber + OBRIEN_BASHIR_RECOVERY_TURNS;'
s=s.replace(needle, needle + '\n    printf("OBRDBG schedule p=%li abs=%lu ret=%lu playback=%d\\n", rogue.playerTurnNumber, rogue.absoluteTurnNumber, obrienBashirReturnTurn, rogue.playbackMode);')
needle2='''    if (obrienBashirReturnTurn
        && rogue.absoluteTurnNumber >= obrienBashirReturnTurn
        && obrienFindLivingCrew("Bashir") == NULL) {

        obrienBashirReturnTurn = 0;'''
repl2='''    if (rogue.playerTurnNumber >= 4000 && rogue.playerTurnNumber <= 4060) {
        printf("OBRDBG maint p=%li abs=%lu ret=%lu bashir=%p playback=%d\\n",
               rogue.playerTurnNumber, rogue.absoluteTurnNumber, obrienBashirReturnTurn,
               (void *) obrienFindLivingCrew("Bashir"), rogue.playbackMode);
    }

    if (obrienBashirReturnTurn
        && rogue.absoluteTurnNumber >= obrienBashirReturnTurn
        && obrienFindLivingCrew("Bashir") == NULL) {

        printf("OBRDBG return p=%li abs=%lu ret=%lu playback=%d\\n",
               rogue.playerTurnNumber, rogue.absoluteTurnNumber, obrienBashirReturnTurn, rogue.playbackMode);
        obrienBashirReturnTurn = 0;'''
if needle2 not in s:
    raise SystemExit("maintenance anchor missing")
s=s.replace(needle2,repl2,1)
p.write_text(s)
print("forensic instrumentation applied")
