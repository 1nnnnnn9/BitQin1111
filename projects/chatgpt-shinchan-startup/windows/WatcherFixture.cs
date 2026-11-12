using System;
using System.Drawing;
using System.Runtime.InteropServices;
using System.Windows.Forms;
class WatcherFixture {
 [DllImport("user32.dll")]static extern bool ShowWindow(IntPtr hwnd,int how);
 static void Display(Form form){form.Show();ShowWindow(form.Handle,5);form.Activate();}
 static Form Window(){var form=new Form{Text="Startup watcher test fixture",ClientSize=new Size(960,600),StartPosition=FormStartPosition.CenterScreen};form.Controls.Add(new Label{Text="Synthetic window for the startup animation test.\nNo ChatGPT process is started, stopped or modified.",Dock=DockStyle.Fill,TextAlign=ContentAlignment.MiddleCenter});return form;}
 [STAThread]static void Main(string[] args){
  Application.EnableVisualStyles();var context=new ApplicationContext();var form=Window();var timer=new Timer{Interval=500};int ticks=0;
  int duration=15000;int i=Array.IndexOf(args,"--duration-ms");if(i>=0&&i+1<args.Length)duration=int.Parse(args[i+1]);
  bool exercise=Array.IndexOf(args,"--exercise-reactivation")>=0;Form extra=null;
  timer.Tick+=(s,e)=>{
   ticks++;if(ticks==2)Display(form);
   if(exercise){
    if(ticks==30)form.WindowState=FormWindowState.Minimized;
    if(ticks==32){form.WindowState=FormWindowState.Normal;form.Activate();}
    if(ticks==34)form.Hide();
    if(ticks==36)Display(form);
    if(ticks==38){extra=Window();Display(extra);}
    if(ticks==40){form.Dispose();form=Window();Display(form);}
   }
   if(ticks*500>=duration){timer.Stop();form.Dispose();if(extra!=null)extra.Dispose();context.ExitThread();}
  };timer.Start();Application.Run(context);timer.Dispose();
 }
}
