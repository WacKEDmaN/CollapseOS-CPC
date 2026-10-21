-- env var CPC_STEPS = "frame|text@@frame|text@@frame|SNAP@@..."
-- text: \n = Enter, \b = DEL. Commands: SNAP EXIT REGS "DBG <cmd>" "DUMP <hexaddr> <hexlen> <file>"
local steps={}
for item in string.gmatch(os.getenv("CPC_STEPS").."@@","(.-)@@") do
  local f,t=string.match(item,"^(%d+)|(.*)$")
  table.insert(steps,{tonumber(f),t})
end
local frames=0
local idx=1
emu.register_frame_done(function()
  frames=frames+1
  while idx<=#steps and frames>=steps[idx][1] do
    local t=steps[idx][2]
    if t=="SNAP" then manager.machine.video:snapshot()
    elseif t=="EXIT" then manager.machine:exit()
    elseif string.sub(t,1,4)=="DBG " then
      manager.machine.debugger:command(string.sub(t,5))
    elseif t=="REGS" then
      local st=manager.machine.devices[":maincpu"].state
      print(string.format("frame %d PC=%04x SP=%04x AF=%04x BC=%04x DE=%04x HL=%04x IX=%04x IY=%04x",frames,st["PC"].value,st["SP"].value,st["AF"].value,st["BC"].value,st["DE"].value,st["HL"].value,st["IX"].value,st["IY"].value))
    elseif string.sub(t,1,5)=="DUMP " then
      local a,n,fn=string.match(t,"DUMP (%x+) (%x+) (.+)")
      a=tonumber(a,16); n=tonumber(n,16)
      local mem=manager.machine.devices[":maincpu"].spaces["program"]
      local f=io.open(fn,"wb")
      for i=0,n-1 do f:write(string.char(mem:read_u8(a+i))) end
      f:close()
    else manager.machine.natkeyboard:post((t:gsub("\\n","\n"):gsub("\\b","\b"))) end
    idx=idx+1
  end
end)
