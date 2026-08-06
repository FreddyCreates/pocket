!macro customInstall
  CreateDirectory "$SMPROGRAMS\POCKET"
  CreateShortCut "$DESKTOP\POCKET Edge.lnk" "$INSTDIR\POCKET.exe" "--edge" "$INSTDIR\POCKET.exe" 0 SW_SHOWNORMAL "" "Open POCKET as a Microsoft Edge app"
  CreateShortCut "$SMPROGRAMS\POCKET\POCKET Edge.lnk" "$INSTDIR\POCKET.exe" "--edge" "$INSTDIR\POCKET.exe" 0 SW_SHOWNORMAL "" "Open POCKET as a Microsoft Edge app"
  CreateShortCut "$SMPROGRAMS\POCKET\POCKET Cloud.lnk" "$INSTDIR\POCKET.exe" "--cloud" "$INSTDIR\POCKET.exe" 0 SW_SHOWNORMAL "" "Open the always-on POCKET Cloud account"
  CreateShortCut "$SMPROGRAMS\POCKET\POCKET Local.lnk" "$INSTDIR\POCKET.exe" "--local" "$INSTDIR\POCKET.exe" 0 SW_SHOWNORMAL "" "Open the packaged local POCKET engine"
!macroend

!macro customUnInstall
  Delete "$DESKTOP\POCKET Edge.lnk"
  Delete "$SMPROGRAMS\POCKET\POCKET Edge.lnk"
  Delete "$SMPROGRAMS\POCKET\POCKET Cloud.lnk"
  Delete "$SMPROGRAMS\POCKET\POCKET Local.lnk"
  RMDir "$SMPROGRAMS\POCKET"
!macroend
