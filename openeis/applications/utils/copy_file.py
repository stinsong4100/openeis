"""Copy files directly, i.e., without looking at contents."""


#--- Provide access.
#
import os
import shutil


def ensureDir(dirName):
    """
    Create a directory if necessary.

    **Args:**

    - *dirName*, path to directory.

    **Returns:**

    - ``True`` if created directory.
    - ``False`` if directory already exists.

    **Raises:**

    - If *dirName* cannot be created.
    - If *dirName* names an existing file.

    **Notes:**

    - *dirName* can give an absolute or relative path.
    - *srcFileName* can name intermediate directories.  For example, creating "mid/final"
      creates directory "mid" if necessary.
    """
    #
    if( os.path.isdir(dirName) ):
        return( False )
    #
    # Here, need to create directory.
    #   Note if *dirName* names an existing file, this will raise an exception.
    os.makedirs(dirName)
    #
    return( True )
    #
    # End :func:`ensureDir`.


def copyFile(srcFileName, destName):
    """
    Copy a file.

    **Args:**

    - *srcFileName*, name of file to copy.
    - *destName*, name of copy.  May be a path, in which case *srcFileName*
      gets copied to the given directory.

    **Returns:**

    - ``True`` if copied file successfully.
    - ``False`` if encounter a textual mistake, e.g., if *srcFileName* does not
      name a file, or if *destName* gives the same file as *srcFileName*.

    **Raises:**

    - If *srcFileName* cannot be copied to *destName*, e.g., because of a
      permissions error.

    **Notes:**

    - File *destName*, if it already exists, will be overwritten.
    - Both *srcFileName* and *destName* may include path information.
    """
    #
    if( (not os.path.isfile(srcFileName))
        or
        (os.path.abspath(srcFileName)==os.path.abspath(destName)) ):
        return( False )
    #
    destDirName = os.path.dirname(destName)
    if( len(destDirName) > 0 ):
        ensureDir(destDirName)
    #
    shutil.copy(srcFileName, destName)
    #
    return( True )
    #
    # End :func:`copyFile`.


def copyAllFiles(srcDirName, destDirName):
    """
    Copy all files in one directory to another.

    **Args:**

    - *srcDirName*, name of directory from which to copy files.
    - *destDirName*, name of receiving directory.

    **Returns:**

    - ``True`` if copied files successfully.
    - ``False`` if encounter a textual mistake, e.g., if *srcDirName* does not
      name a directory, or if *destDirName* gives the same directory as *srcDirName*.

    **Raises:**

    - For external error, e.g., a permissions error.

    **Notes:**

    - Any existing file in *destDirName* will be overwritten by a file with
      the same name in *srcDirName*.
    - Copy only files-- do not descend into subdirectories of *srcDirName*.
    """
    #
    if( (not os.path.isdir(srcDirName))
        or
        (os.path.abspath(srcDirName)==os.path.abspath(destDirName))
        or
        (os.path.isfile(destDirName)) ):
        return( False )
    #
    ensureDir(destDirName)
    #
    for baseName in os.listdir(srcDirName):
        srcFileName = os.path.join(srcDirName, baseName)
        if( os.path.isfile(srcFileName) ):
            destFileName = os.path.join(destDirName, baseName)
            shutil.copy(srcFileName, destFileName)
    #
    return( True )
    #
    # End :func:`copyAllFiles`.
