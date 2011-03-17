def vcompare(ver, upstream_ver):
    '''Compare versions int by int'''
    ver_split = ver.split('.')
    upsteram_ver_split = upstream_ver.split('.')
    count = 0
    for i in upsteram_ver_split:
        if ver_split[count] == upsteram_ver_split[count]:
            count += 1
            continue
        else:
            if int(ver_split[count]) < int(upsteram_ver_split[count]):
                return upstream_ver
            else:
                break
