def check_admin [] {
    if (is-admin) {
        return true
    } else {
        error make {msg: "Run it as admin.", }
    }
}

check_admin

# Disable Adobe Background Processes
def main [] {
    ps | where name == "CCXProcess.exe" | each {|e| kill -f $e.pid}
    ps | where name == "CoreSync.exe" | each {|e| kill -f $e.pid}
    ps | where name == "Adobe Desktop Service.exe" | each {|e| kill -f $e.pid}
    ps | where name == "CCLibrary.exe" | each {|e| kill -f $e.pid}
    ps | where name == "AdobeCollabSync.exe" | each {|e| kill -f $e.pid}

    # PS
    mv 'C:\Program Files (x86)\Adobe\Adobe Sync\CoreSync\CoreSync.exe' 'C:\Program Files (x86)\Adobe\Adobe Sync\CoreSync\CoreSync.exe.bak'
    mv 'C:\Program Files\Adobe\Adobe Creative Cloud Experience\CCXProcess.exe' 'C:\Program Files\Adobe\Adobe Creative Cloud Experience\CCXProcess.exe.bak'
    mv 'C:\Program Files (x86)\Common Files\Adobe\Adobe Desktop Common\ADS\Adobe Desktop Service.exe' 'C:\Program Files (x86)\Common Files\Adobe\Adobe Desktop Common\ADS\Adobe Desktop Service.exe.bak'
    mv 'C:\Program Files\Common Files\Adobe\Creative Cloud Libraries\CCLibrary.exe' 'C:\Program Files\Common Files\Adobe\Creative Cloud Libraries\CCLibrary.exe.bak'

    # Acrobat
    mv 'C:\Program Files\Adobe\Acrobat DC\Acrobat\AdobeCollabSync.exe' 'C:\Program Files\Adobe\Acrobat DC\Acrobat\AdobeCollabSync.exe.bak'
}


def "main restore" [
] {
    mv 'C:\Program Files (x86)\Adobe\Adobe Sync\CoreSync\CoreSync.exe.bak' 'C:\Program Files (x86)\Adobe\Adobe Sync\CoreSync\CoreSync.exe'
    mv 'C:\Program Files\Adobe\Adobe Creative Cloud Experience\CCXProcess.exe.bak' 'C:\Program Files\Adobe\Adobe Creative Cloud Experience\CCXProcess.exe'
    mv 'C:\Program Files (x86)\Common Files\Adobe\Adobe Desktop Common\ADS\Adobe Desktop Service.exe.bak' 'C:\Program Files (x86)\Common Files\Adobe\Adobe Desktop Common\ADS\Adobe Desktop Service.exe'
    mv 'C:\Program Files\Common Files\Adobe\Creative Cloud Libraries\CCLibrary.exe.bak' 'C:\Program Files\Common Files\Adobe\Creative Cloud Libraries\CCLibrary.exe'

    mv 'C:\Program Files\Adobe\Acrobat DC\Acrobat\AdobeCollabSync.exe.bak' 'C:\Program Files\Adobe\Acrobat DC\Acrobat\AdobeCollabSync.exe'
}