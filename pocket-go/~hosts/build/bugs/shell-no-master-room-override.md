---
crate: crate.A713875AD578BE79
title: this-bugs-me - new shell cannot claim master of room / still falls into prior paper
status: open
kind: this-bugs-me
reported: 2026-09-15
by: Kitten
where: PocketGo shells / subshell / paper
---

# New shell cannot fully override prior shell subshell position

## Itch
It bugs Kitten that there is no way for a new shell to say it does not want to fall into the previous shell's subshell position. The new shell still goes into the paper anyway. It does not fully override. There is no way to say this shell becomes the total master of the room - the system still first tries to stick it inside of the paper.

## Expected / wanted
A way for a new shell to opt out of nesting in the previous shell's paper / subshell slot, and instead take full mastery of the room (total override), rather than always attempting to land inside the prior paper first.

## Notes
Wish-it-could-be-better / missing control, not a one-off breakage report. Parked for later Cursor harness. Soft-dump to Hop. Do not mid-session platform-edit.