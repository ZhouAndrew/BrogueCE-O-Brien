set pagination off
set confirm off
set breakpoint pending on

# A clean replay mismatch must fail immediately instead of falling into the
# interactive playback-panic path of an ordinary save load.
break playbackPanic
commands
  silent
  printf "CLEAN_VERIFY_PLAYBACK_PANIC turn=%ld hp=%d ended=%d oos=%d\n", rogue.playerTurnNumber, player.currentHP, rogue.gameHasEnded, rogue.playbackOOS
  quit 92
end

# loadSavedGame() calls switchToPlaying() only after its replay loop has
# completed without gameHasEnded or playbackOOS. Stop before switchToPlaying
# mutates playback state and inspect the untouched clean-v0.2.28 engine.
break switchToPlaying
commands
  silent
  printf "CLEAN_VERIFY_FINAL turn=%ld hp=%d ended=%d oos=%d\n", rogue.playerTurnNumber, player.currentHP, rogue.gameHasEnded, rogue.playbackOOS
  if rogue.playerTurnNumber != 3727
    printf "CLEAN_VERIFY_FAIL bad_turn\n"
    quit 93
  end
  if player.currentHP <= 0
    printf "CLEAN_VERIFY_FAIL dead_player\n"
    quit 94
  end
  if rogue.gameHasEnded != 0
    printf "CLEAN_VERIFY_FAIL game_ended\n"
    quit 95
  end
  if rogue.playbackOOS != 0
    printf "CLEAN_VERIFY_FAIL oos\n"
    quit 96
  end
  printf "CLEAN_VERIFY_PASS\n"
  quit 0
end

run -o migrated.broguesave
