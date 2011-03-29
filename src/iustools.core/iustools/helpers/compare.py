
def vcompare(upstream, downstream):
    """
    Compare versions int by int.   Returns True if the versions are the same,
    False other wise.
    
    Required Arguments:
    
        upstream
            The upstream version of a package to compare
            
        downstream
            The downstream version of a package to compare
        
    Returns: Bool
       
    """
    upstream_split = upstream.split('.')
    downstream_split = downstream.split('.')
    count = 0
    for i in upstream_split:
        if downstream_split[count] == upstream_split[count]:
            count += 1
            continue
        else:
            if int(downstream_split[count]) < int(upstream_split[count]):
                return False
            else:
                break

    return True