# 链接文件
def main [] {
  if (is-admin) {
    let $kernel_name = (uname | get kernel-name)
    if $kernel_name == "Windows_NT" {
      for e in (open linkfiles.toml | get files) {
        let src = ($e.src | path expand);
        let linkto = ($e.linkto | path expand);
        mkdir -v $'($linkto | path dirname)';
        do -i { mklink $linkto $src; }
      }
    } else if $kernel_name == "Linux" {
      for e in (open linkfiles.toml | get files) {
        let src = ($e.src | path expand);
        let linkto = ($e.linkto | path expand);
        mkdir -v $'($linkto | path dirname)';
        do -i { ln -s $linkto $src; }
      }
    } else {
      print "Unknown system" 
    }
  } else {
    print "Run it as admin."
  }
}

# 添加链接文件路径至配置文件
def "main addPath" [
  src: path # 源文件路径
  linkto: path # 链接至的路径
] {
  if (checkTomlExists) {
    open linkfiles.toml | update files {append {src: $src, linkto: $linkto}} | save -f linkfiles.toml
  } else {
    {"files": [{src: $src, linkto: $linkto}]} | save linkfiles.toml
  }
}

# 删除链接文件
def "main remove" [] {
  if not (checkTomlExists) {
    error make {msg: "linkfiles.toml doesn't exist"}
  }

  if (is-admin) {
      for f in (open linkfiles.toml | get files.linkto) {
        let $r = powershell rm $f | complete # Why not use built-in rm: https://github.com/nushell/nushell/issues/11652
        if $r.exit_code == 0 {
          print $"Remove (ansi green)($f)(ansi reset) successfully"
        } else {
          print -e $"(ansi red)($r.stderr | decode gbk)(ansi reset)"
        }
      }
  } else {
    print "Run it as admin."
  }
  
}

def checkTomlExists [] {
  return ("./linkfiles.toml" | path exists)
}
