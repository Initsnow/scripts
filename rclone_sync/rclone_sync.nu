#!/usr/bin/env nu
let $ping_output = do -i { ping -n 1 8.8.4.4 } | complete

def --env get_pwd [] {
  print "Input your rclone configiration password:"
  let pwd = (input -s)
  $env.RCLONE_CONFIG_PASS = $pwd
}

#Synchronize local files with remote path
def "main sync" [] {
  get_pwd
  if $ping_output.exit_code == 0 {
    print "Internet connection is OK"
    for e in (open paths.toml | get path | transpose local remote) {
      if ($e.remote|describe) == list<string> {
        sync $e.local $e.remote.0 $e.remote.1
      } else {
        sync $e.local $e.remote
      }
    }
  } else {
    print "Unable to connect to the internet!"
    print $"Ping output:($ping_output.stdout)"
  }
}

def sync [path:path,remotepath:string,remote?:string] {
  if $remote == null {
    for e in (open paths.toml | get remote) {
      print $"\n($path) is syncing to ($e):($remotepath)"
      rclone sync -P $path $'($e):($remotepath)'
    }
  } else {
    print $"\n($path) is syncing to ($remote):($remotepath)"
    rclone sync -P $path $'($remote):($remotepath)'
  }
}

#Copy files in the remote path to the specified directory
def "main pull" [
  remote_index:number = 1
] {
  get_pwd
  if $ping_output.exit_code == 0 {
    print "Internet connection is OK"
    open paths.toml | get path | transpose local remote | each {|e| pull $e.remote $e.local $remote_index}
  } else {
    print "Unable to connect to the internet!"
    print $"Ping output:($ping_output.stdout)"
  }
}

def pull [remotepath:string,path:path,remote_index:int] {
  let remote = $env.RCLONE_CONFIG_PASS
  print $"\n($remote):($remotepath) is copying to ($path)"
  rclone copy -P $'($remote):($remotepath)' $path
}

def main [] {}
