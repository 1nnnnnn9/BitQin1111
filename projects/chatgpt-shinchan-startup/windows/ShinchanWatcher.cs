using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Linq;
using System.Media;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Forms;
using Microsoft.Web.WebView2.Core;
using Microsoft.Web.WebView2.WinForms;

static class Win {
 internal delegate void EventProc(IntPtr hook,uint kind,IntPtr hwnd,int obj,int child,uint thread,uint time);
 internal delegate bool EnumProc(IntPtr hwnd,IntPtr data);
 [StructLayout(LayoutKind.Sequential)] internal struct Rect {public int Left,Top,Right,Bottom;}
 [StructLayout(LayoutKind.Sequential)] internal struct Point {public int X,Y;}
 [DllImport("user32.dll")] internal static extern IntPtr SetWinEventHook(uint min,uint max,IntPtr module,EventProc callback,uint process,uint thread,uint flags);
 [DllImport("user32.dll")] internal static extern bool UnhookWinEvent(IntPtr hook);
 [DllImport("user32.dll")] internal static extern bool EnumWindows(EnumProc callback,IntPtr data);
 [DllImport("user32.dll")] internal static extern bool IsWindow(IntPtr hwnd);
 [DllImport("user32.dll")] internal static extern bool IsWindowVisible(IntPtr hwnd);
 [DllImport("user32.dll")] internal static extern bool IsIconic(IntPtr hwnd);
 [DllImport("user32.dll")] internal static extern IntPtr GetAncestor(IntPtr hwnd,uint flags);
 [DllImport("user32.dll")] internal static extern IntPtr GetWindow(IntPtr hwnd,uint command);
 [DllImport("user32.dll")] internal static extern int GetWindowLong(IntPtr hwnd,int index);
 [DllImport("user32.dll")] internal static extern bool GetWindowRect(IntPtr hwnd,out Rect rect);
 [DllImport("user32.dll")] internal static extern bool GetClientRect(IntPtr hwnd,out Rect rect);
 [DllImport("user32.dll")] internal static extern bool ClientToScreen(IntPtr hwnd,ref Point point);
 [DllImport("user32.dll")] internal static extern uint GetWindowThreadProcessId(IntPtr hwnd,out uint pid);
 [DllImport("user32.dll")] internal static extern IntPtr GetForegroundWindow();
 [DllImport("user32.dll")] internal static extern bool SetForegroundWindow(IntPtr hwnd);
 [DllImport("user32.dll")] internal static extern bool ShowWindow(IntPtr hwnd,int how);
 [DllImport("user32.dll")] internal static extern bool SetWindowPos(IntPtr hwnd,IntPtr after,int x,int y,int width,int height,uint flags);
 [DllImport("user32.dll")] internal static extern bool SetProcessDpiAwarenessContext(IntPtr value);
 [DllImport("kernel32.dll")] internal static extern IntPtr OpenProcess(uint access,bool inherit,uint pid);
 [DllImport("kernel32.dll")] internal static extern bool CloseHandle(IntPtr process);
 [DllImport("kernel32.dll",CharSet=CharSet.Unicode)] internal static extern int GetPackageFamilyName(IntPtr process,ref uint length,StringBuilder name);
 [DllImport("kernel32.dll",CharSet=CharSet.Unicode)] internal static extern bool QueryFullProcessImageName(IntPtr process,uint flags,StringBuilder name,ref int length);
 internal static Rectangle Client(IntPtr hwnd){Rect r;Point p=new Point();if(!GetClientRect(hwnd,out r)||!ClientToScreen(hwnd,ref p))return Rectangle.Empty;return new Rectangle(p.X,p.Y,r.Right-r.Left,r.Bottom-r.Top);}
 internal static bool MatchesProcess(uint pid,string fixture){
  IntPtr process=OpenProcess(0x1000,false,pid);if(process==IntPtr.Zero)return false;
  try {
   var path=new StringBuilder(4096);int length=path.Capacity;if(!QueryFullProcessImageName(process,0,path,ref length))return false;
   if(fixture!=null)return String.Equals(Path.GetFullPath(path.ToString()),fixture,StringComparison.OrdinalIgnoreCase);
   if(!String.Equals(Path.GetFileName(path.ToString()),"ChatGPT.exe",StringComparison.OrdinalIgnoreCase))return false;
   uint count=512;var family=new StringBuilder((int)count);
   return GetPackageFamilyName(process,ref count,family)==0&&family.ToString()=="OpenAI.Codex_2p2nqsd0c76g0";
  }finally{CloseHandle(process);}
 }
 internal static HashSet<string> RunningInstances(string fixture){
  var result=new HashSet<string>();
  string name=fixture==null?"ChatGPT":Path.GetFileNameWithoutExtension(fixture);
  foreach(var process in Process.GetProcessesByName(name)){
   using(process){try{if(MatchesProcess((uint)process.Id,fixture))result.Add(process.Id+":"+process.StartTime.ToUniversalTime().Ticks);}catch(InvalidOperationException){}catch(System.ComponentModel.Win32Exception){}}
  }
  return result;
 }
 internal static bool Eligible(IntPtr hwnd,string fixture){
  if(hwnd==IntPtr.Zero||!IsWindow(hwnd)||!IsWindowVisible(hwnd)||IsIconic(hwnd)||GetAncestor(hwnd,2)!=hwnd||GetWindow(hwnd,4)!=IntPtr.Zero||(GetWindowLong(hwnd,-20)&0x80)!=0)return false;
  Rectangle size=Client(hwnd);if(size.Width<450||size.Height<280)return false;
  uint pid;GetWindowThreadProcessId(hwnd,out pid);return MatchesProcess(pid,fixture);
 }
}
static class State {
 internal static string Root,Data,StopName;
 internal static string Option(string[] args,string flag){int n=Array.IndexOf(args,flag);return n>=0&&n+1<args.Length?args[n+1]:null;}
 internal static void Log(string text){try{Directory.CreateDirectory(Data);File.AppendAllText(Path.Combine(Data,"watcher.log"),DateTime.Now.ToString("s")+" "+text+Environment.NewLine);}catch{}}
}
sealed class MovieForm : Form {
 readonly WebView2 view=new WebView2();readonly IntPtr source;readonly bool preview;
 readonly SoundPlayer greeting=new SoundPlayer();bool greetingPlayed,originalSoundtrack;
 readonly System.Windows.Forms.Timer timeout=new System.Windows.Forms.Timer{Interval=35000};
 readonly System.Windows.Forms.Timer fade=new System.Windows.Forms.Timer{Interval=16};
 readonly Stopwatch exitClock=new Stopwatch();readonly Stopwatch playback=new Stopwatch();bool started,finished;Rectangle lastBounds;
 internal MovieForm(IntPtr target,bool isPreview){
  source=target;preview=isPreview;Text="ChatGPT · 蜡笔小新开场";FormBorderStyle=FormBorderStyle.None;ShowInTaskbar=isPreview;
  StartPosition=FormStartPosition.Manual;BackColor=Color.FromArgb(8,6,13);KeyPreview=true;TopMost=true;
  Rectangle area=Screen.FromPoint(Cursor.Position).WorkingArea;
  Bounds=target!=IntPtr.Zero?Win.Client(target):new Rectangle(area.Left+(area.Width-Math.Min(1120,area.Width))/2,area.Top+(area.Height-Math.Min(700,area.Height))/2,Math.Min(1120,area.Width),Math.Min(700,area.Height));
  lastBounds=Bounds;view.Dock=DockStyle.Fill;view.DefaultBackgroundColor=BackColor;Controls.Add(view);
  KeyDown+=(s,e)=>{if(e.KeyCode==Keys.Escape){e.Handled=true;Finish("skipped");}};
  timeout.Tick+=(s,e)=>Finish("prepare-timeout");
  fade.Tick+=(s,e)=>{
   if(source!=IntPtr.Zero&&(!Win.IsWindow(source)||Win.IsIconic(source))){Finish("source-unavailable");return;}
   if(exitClock.IsRunning){double p=Math.Min(1,exitClock.Elapsed.TotalSeconds/.85);Opacity=1-p*p*(3-2*p);}
   else if(source!=IntPtr.Zero){Rectangle b=Win.Client(source);if(!b.IsEmpty&&b!=lastBounds){Bounds=b;lastBounds=b;}}
  };
  FormClosed+=(s,e)=>{greeting.Stop();greeting.Dispose();timeout.Dispose();fade.Dispose();view.Dispose();};
 }
 internal async void Prepare(){
  try {
   // WebView2 initialization and image decoding may stall in a never-shown host.
   // Explicit Win32 show also overrides the hidden startup state of the watcher.
   IntPtr handle=Handle;Show();Win.ShowWindow(handle,5);
   Win.SetWindowPos(handle,new IntPtr(-1),Left,Top,Width,Height,0x0040);
   view.CreateControl();timeout.Start();
   string audio=Path.Combine(State.Root,"assets","startup-original.wav");originalSoundtrack=File.Exists(audio);
   if(!originalSoundtrack)audio=Path.Combine(State.Root,"assets","welcome-home.wav");
   if(File.Exists(audio)){try{greeting.SoundLocation=audio;greeting.Load();}catch(Exception error){State.Log("sound-load-failed "+error.Message);}}
   State.Log("player-host-visible="+Win.IsWindowVisible(handle)+" bounds="+Bounds);
   var env=await CoreWebView2Environment.CreateAsync(null,Path.Combine(State.Data,"webview"));
   await view.EnsureCoreWebView2Async(env);
   State.Log("webview-initialized");
   view.CoreWebView2.Settings.AreDefaultContextMenusEnabled=false;
   view.CoreWebView2.Settings.IsStatusBarEnabled=false;
   view.CoreWebView2.SetVirtualHostNameToFolderMapping("startup.local",State.Root,CoreWebView2HostResourceAccessKind.DenyCors);
   view.CoreWebView2.NavigationStarting+=(s,e)=>{if(!e.Uri.StartsWith("https://startup.local/",StringComparison.OrdinalIgnoreCase)&&e.Uri!="about:blank")e.Cancel=true;};
   view.CoreWebView2.AddWebResourceRequestedFilter("*",CoreWebView2WebResourceContext.All);
   view.CoreWebView2.WebResourceRequested+=(s,e)=>{string uri=e.Request.Uri;if(!uri.StartsWith("https://startup.local/",StringComparison.OrdinalIgnoreCase)&&!uri.StartsWith("data:",StringComparison.OrdinalIgnoreCase)&&!uri.StartsWith("blob:",StringComparison.OrdinalIgnoreCase)&&uri!="about:blank")e.Response=env.CreateWebResourceResponse(new MemoryStream(),403,"Local animation only","");};
   await view.CoreWebView2.AddScriptToExecuteOnDocumentCreatedAsync("window.AEMEATH_PREWARM=true;window.addEventListener('error',e=>window.chrome.webview.postMessage('script-error:'+e.message));window.addEventListener('DOMContentLoaded',()=>document.body.classList.add('watch-mode'));");
   view.CoreWebView2.NavigationCompleted+=(s,e)=>State.Log("navigation-success="+e.IsSuccess+" status="+e.WebErrorStatus);
   view.CoreWebView2.ProcessFailed+=(s,e)=>{State.Log("webview-process-failed "+e.ProcessFailedKind);Finish("webview-process-failed");};
   view.CoreWebView2.WebMessageReceived+=OnMessage;
   view.CoreWebView2.Navigate("https://startup.local/index.html?watcher=1");
  }catch(Exception e){State.Log("player-error "+e.GetType().Name+" "+e.Message);Finish("failed");}
 }
 async void OnMessage(object sender,CoreWebView2WebMessageReceivedEventArgs e){
  try {
   if(!e.Source.StartsWith("https://startup.local/",StringComparison.OrdinalIgnoreCase))return;
   string message=e.TryGetWebMessageAsString();
   if(message.StartsWith("script-error:")){State.Log(message);return;}
   if(message=="ready"&&!started){
    started=true;timeout.Stop();timeout.Interval=18000;timeout.Start();
    if(source!=IntPtr.Zero&&(!Win.IsWindow(source)||Win.IsIconic(source))){Finish("source-unavailable");return;}
    Show();Win.ShowWindow(Handle,5);Win.SetWindowPos(Handle,new IntPtr(-1),Left,Top,Width,Height,0x0040);
    Activate();view.Focus();fade.Start();playback.Start();
    await view.CoreWebView2.ExecuteScriptAsync("window.launcherUI.beginLaunch(false)");
    State.Log((preview?"preview-playing":"original-entry-animation-playing")+" visible="+Win.IsWindowVisible(Handle));
   }else if(message=="reveal"){if(!exitClock.IsRunning)exitClock.Start();}
   else if(message=="typing-sound"&&started&&!greetingPlayed){
    greetingPlayed=true;
    if(!String.IsNullOrEmpty(greeting.SoundLocation)){try{greeting.Play();State.Log((originalSoundtrack?"startup-original-started":"typing-sound-played")+" playback-ms="+playback.ElapsedMilliseconds);}catch(Exception error){State.Log("sound-play-failed "+error.Message);}}
   }
   else if(message=="complete")Finish("complete");
   else if(message=="assetError")Finish("asset-error");
  }catch(Exception ex){State.Log("message-error "+ex.GetType().Name);Finish("failed");}
 }
 void Finish(string outcome){
  if(finished)return;finished=true;timeout.Stop();fade.Stop();greeting.Stop();
  bool restore=source!=IntPtr.Zero&&Win.IsWindow(source)&&!Win.IsIconic(source)&&Win.GetForegroundWindow()==Handle;
  State.Log("animation-"+outcome+" playback-ms="+playback.ElapsedMilliseconds);Close();if(restore)Win.SetForegroundWindow(source);
 }
}
sealed class Watcher : ApplicationContext {
 readonly Win.EventProc callback;readonly List<IntPtr> hooks=new List<IntPtr>();
 readonly HashSet<IntPtr> known=new HashSet<IntPtr>();readonly Dictionary<IntPtr,DateTime> pending=new Dictionary<IntPtr,DateTime>();
 HashSet<string> runningInstances=new HashSet<string>();bool launchConsumed;
 readonly System.Windows.Forms.Timer probe=new System.Windows.Forms.Timer{Interval=180};
 readonly System.Windows.Forms.Timer stopTimer=new System.Windows.Forms.Timer{Interval=500};
 readonly EventWaitHandle stop;readonly string fixture;readonly Stopwatch life=new Stopwatch();readonly int duration;
 MovieForm active;readonly uint ownPid=(uint)Process.GetCurrentProcess().Id;
 internal Watcher(string[] args){
  string test=State.Option(args,"--fixture");fixture=test==null?null:Path.GetFullPath(test);
  int.TryParse(State.Option(args,"--watch-ms"),out duration);
  stop=new EventWaitHandle(false,EventResetMode.ManualReset,State.StopName);stop.Reset();
  RefreshSession();launchConsumed=runningInstances.Count>0;
  if(launchConsumed)State.Log("existing-app-session-seeded instances="+runningInstances.Count);
  Win.EnumWindows((h,d)=>{if(Win.Eligible(h,fixture))known.Add(h);return true;},IntPtr.Zero);
  callback=OnEvent;
  hooks.Add(Win.SetWinEventHook(0x8001,0x8003,IntPtr.Zero,callback,0,0,2));
  hooks.Add(Win.SetWinEventHook(3,3,IntPtr.Zero,callback,0,0,2));
  if(hooks.Any(h=>h==IntPtr.Zero))throw new InvalidOperationException("Window event hook could not be installed");
  probe.Tick+=Probe;stopTimer.Tick+=(s,e)=>{RefreshSession();if(stop.WaitOne(0)||(duration>0&&life.ElapsedMilliseconds>=duration))ExitThread();};
  life.Start();stopTimer.Start();State.Log(fixture==null?"watcher-ready original-system-entry cold-start-only":"fixture-watcher-ready cold-start-only");
 }
 void RefreshSession(){
  var current=Win.RunningInstances(fixture);
  // Window visibility is unrelated to application lifetime. PID + creation time
  // also handles a full quit/relaunch between two timer samples and PID reuse.
  if(current.Count==0||(runningInstances.Count>0&&!current.Overlaps(runningInstances)))launchConsumed=false;
  runningInstances=current;
 }
 void OnEvent(IntPtr hook,uint kind,IntPtr hwnd,int obj,int child,uint thread,uint time){
  if(hwnd==IntPtr.Zero||obj!=0||child!=0)return;
  uint pid;Win.GetWindowThreadProcessId(hwnd,out pid);if(pid==ownPid)return;
  if(kind==0x8001){known.Remove(hwnd);pending.Remove(hwnd);return;}
  if(kind==0x8003){pending.Remove(hwnd);return;}
  if(known.Contains(hwnd)||pending.ContainsKey(hwnd))return;
  if(Win.Eligible(hwnd,fixture)){pending[hwnd]=DateTime.UtcNow;probe.Start();}
 }
 void Probe(object sender,EventArgs e){
  foreach(var entry in pending.ToArray()){
   if((DateTime.UtcNow-entry.Value).TotalSeconds<.2)continue;
   pending.Remove(entry.Key);IntPtr hwnd=entry.Key;
   if(!Win.Eligible(hwnd,fixture))continue;known.Add(hwnd);
   RefreshSession();
   if(launchConsumed){State.Log("activation-ignored app-session-already-running");continue;}
   if(active!=null)continue;launchConsumed=true;
   State.Log("cold-start-detected");
   active=new MovieForm(hwnd,false);active.FormClosed+=(s,closed)=>{active=null;};active.Prepare();
  }
  if(pending.Count==0)probe.Stop();
 }
 protected override void ExitThreadCore(){
  foreach(IntPtr hook in hooks)if(hook!=IntPtr.Zero)Win.UnhookWinEvent(hook);
  if(active!=null)active.Close();probe.Dispose();stopTimer.Dispose();stop.Dispose();State.Log("watcher-stopped");base.ExitThreadCore();
 }
}
static class Program {
 [STAThread] static int Main(string[] args){
  State.Root=State.Option(args,"--assets")??AppDomain.CurrentDomain.BaseDirectory.TrimEnd('\\');
  if(!File.Exists(Path.Combine(State.Root,"index.html")))State.Root=Path.GetFullPath(Path.Combine(State.Root,"..",".."));
  State.Data=State.Option(args,"--state")??Path.Combine(State.Root,".state");Directory.CreateDirectory(State.Data);
  State.StopName=args.Contains("--fixture")?"Local\\ShinchanStartup.Stop.Fixture":"Local\\ShinchanStartup.Stop";
  try {
   if(args.Contains("--stop")){try{using(var stop=EventWaitHandle.OpenExisting(State.StopName))stop.Set();}catch(WaitHandleCannotBeOpenedException){}return 0;}
   if(args.Contains("--diagnose")){int matches=0;Win.EnumWindows((h,d)=>{if(Win.Eligible(h,null))matches++;return true;},IntPtr.Zero);File.WriteAllText(Path.Combine(State.Data,"diagnostic.json"),"{\"eligibleOfficialWindows\":"+matches+",\"assetsAvailable\":"+File.Exists(Path.Combine(State.Root,"assets","shinchan-wide.png")).ToString().ToLowerInvariant()+",\"webViewRuntime\":\""+CoreWebView2Environment.GetAvailableBrowserVersionString()+"\"}");return 0;}
   Win.SetProcessDpiAwarenessContext(new IntPtr(-4));Application.EnableVisualStyles();Application.SetCompatibleTextRenderingDefault(false);
   bool owns;using(var mutex=new Mutex(true,args.Contains("--watch")?(args.Contains("--fixture")?"Local\\ShinchanStartup.Watcher.Fixture":"Local\\ShinchanStartup.Watcher"):"Local\\ShinchanStartup.Preview",out owns)){
    if(!owns)return 0;
    if(args.Contains("--watch"))Application.Run(new Watcher(args));
    else {var context=new ApplicationContext();var form=new MovieForm(IntPtr.Zero,true);form.FormClosed+=(s,e)=>context.ExitThread();form.Prepare();Application.Run(context);}
   }
   return 0;
  }catch(Exception e){State.Log("fatal "+e);return 1;}
 }
}
